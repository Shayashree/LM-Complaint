from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import Product, User, AuditLog
from app.schemas.schemas import ProductResponse, ProductCreate, StandardResponse
from app.core.permissions import PermissionChecker, get_current_user
from datetime import datetime

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR", "SUPERVISOR", "AUDITOR", "ANALYST", "DEPT_ADMIN", "CONSUMER"]))
):
    query = db.query(Product)
    if barcode:
        query = query.filter(Product.barcode == barcode)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            Product.product_name.like(search_filter) | 
            Product.brand.like(search_filter) |
            Product.manufacturer.like(search_filter)
        )
    return query.all()

@router.post("", response_model=ProductResponse)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    if request.barcode:
        existing = db.query(Product).filter(Product.barcode == request.barcode).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with barcode {request.barcode} already exists"
            )
            
    product = Product(
        product_name=request.product_name,
        brand=request.brand,
        category=request.category,
        subcategory=request.subcategory,
        manufacturer=request.manufacturer,
        packer=request.packer,
        importer=request.importer,
        barcode=request.barcode,
        net_quantity=request.net_quantity,
        mrp=request.mrp,
        manufacturing_date=request.manufacturing_date,
        packing_date=request.packing_date,
        consumer_care=request.consumer_care
    )
    db.add(product)
    db.flush()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="PRODUCT_CREATED",
        entity_type="product",
        entity_id=str(product.id),
        timestamp=datetime.utcnow(),
        action_metadata={"barcode": product.barcode}
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    
    return product

@router.get("/{id}", response_model=ProductResponse)
def get_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product SKU not found"
        )
    return product

@router.put("/{id}", response_model=ProductResponse)
def update_product(
    id: int,
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product SKU not found"
        )
        
    for k, v in request.dict(exclude_unset=True).items():
        setattr(product, k, v)
        
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="PRODUCT_UPDATED",
        entity_type="product",
        entity_id=str(product.id),
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(product)
    
    return product
