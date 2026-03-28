from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.db.database import get_db
from app.models.models import Recipe, RecipeIngredient, StockItem, ExpiryDate, User
from app.schemas.schemas import (
    RecipeCreate, RecipeUpdate, RecipeOut,
    CookResult, CookIngredientResult,
)
from app.core.security import get_current_user

router = APIRouter()


def _load_recipe_options():
    return (
        selectinload(Recipe.ingredients).selectinload(RecipeIngredient.product),
    )


async def _get_recipe_or_404(recipe_id: UUID, db: AsyncSession) -> Recipe:
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(*_load_recipe_options())
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    return recipe


@router.get("/recipes", response_model=list[RecipeOut])
async def list_recipes(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(
        select(Recipe)
        .options(*_load_recipe_options())
        .order_by(Recipe.created_at.desc())
    )
    return result.scalars().all()


@router.post("/recipes", response_model=RecipeOut, status_code=201)
async def create_recipe(
    payload: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipe = Recipe(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(recipe)
    await db.flush()

    for ing in payload.ingredients:
        db.add(RecipeIngredient(
            recipe_id=recipe.id,
            product_barcode=ing.product_barcode,
            ingredient_name=ing.ingredient_name,
            quantity=ing.quantity,
            unit=ing.unit,
        ))

    await db.commit()
    return await _get_recipe_or_404(recipe.id, db)


@router.get("/recipes/{recipe_id}", response_model=RecipeOut)
async def get_recipe(recipe_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await _get_recipe_or_404(recipe_id, db)


@router.patch("/recipes/{recipe_id}", response_model=RecipeOut)
async def update_recipe(
    recipe_id: UUID,
    payload: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    recipe = await _get_recipe_or_404(recipe_id, db)

    if payload.name is not None:
        recipe.name = payload.name
    if payload.description is not None:
        recipe.description = payload.description

    if payload.ingredients is not None:
        # Replace all ingredients
        await db.execute(
            sql_delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        )
        for ing in payload.ingredients:
            db.add(RecipeIngredient(
                recipe_id=recipe_id,
                product_barcode=ing.product_barcode,
                ingredient_name=ing.ingredient_name,
                quantity=ing.quantity,
                unit=ing.unit,
            ))

    await db.commit()
    return await _get_recipe_or_404(recipe_id, db)


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    await db.delete(recipe)
    await db.commit()


@router.post("/recipes/{recipe_id}/cook", response_model=CookResult)
async def cook_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    recipe = await _get_recipe_or_404(recipe_id, db)
    results: list[CookIngredientResult] = []

    for ing in recipe.ingredients:
        if ing.product_barcode is None:
            # Ingrédient sans lien produit — on le signale, rien à déduire
            results.append(CookIngredientResult(
                ingredient_name=ing.ingredient_name,
                requested=ing.quantity,
                unit=ing.unit,
                available=0,
                deducted=0,
                status="unlinked",
            ))
            continue

        # Charger les stock items pour ce produit, triés FEFO
        # (expiry date la plus proche d'abord, null en dernier)
        stock_result = await db.execute(
            select(StockItem)
            .where(StockItem.product_barcode == ing.product_barcode)
            .options(selectinload(StockItem.expiry_date))
        )
        stock_items: list[StockItem] = list(stock_result.scalars().all())

        # Trier: items avec DLC d'abord (ASC), sans DLC ensuite
        stock_items.sort(key=lambda s: (
            s.expiry_date is None,
            s.expiry_date.expiry_date if s.expiry_date else None,
        ))

        total_available = sum(s.quantity for s in stock_items)

        remaining_to_deduct = ing.quantity
        actually_deducted = 0.0

        for item in stock_items:
            if remaining_to_deduct <= 0:
                break

            if item.quantity <= remaining_to_deduct:
                # Consomme tout l'article
                actually_deducted += item.quantity
                remaining_to_deduct -= item.quantity
                await db.delete(item)
            else:
                # Consommation partielle de l'article
                item.quantity = round(item.quantity - remaining_to_deduct, 4)
                actually_deducted += remaining_to_deduct
                remaining_to_deduct = 0

        await db.flush()

        if total_available == 0:
            status = "not_in_stock"
        elif actually_deducted < ing.quantity:
            status = "partial"
        else:
            status = "ok"

        results.append(CookIngredientResult(
            ingredient_name=ing.ingredient_name,
            requested=ing.quantity,
            unit=ing.unit,
            available=total_available,
            deducted=actually_deducted,
            status=status,
        ))

    await db.commit()
    return CookResult(recipe_name=recipe.name, results=results)
