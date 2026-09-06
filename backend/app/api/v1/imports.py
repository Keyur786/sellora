from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.schemas.import_reports import ImportResultResponse, COGSImportResponse
from app.integrations.marketplaces.amazon.report_parser import AmazonReportSynchronizer
from app.services.cogs_importer import COGSImporter

router = APIRouter()


@router.post("/amazon/date-range-report", response_model=ImportResultResponse)
async def upload_amazon_date_range_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """
    Upload and parse an official Amazon India Date Range Transaction Report (CSV).
    Extracts orders, line items, and itemized marketplace fees (commissions, closing, shipping, TCS, TDS).
    """
    if not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV or TXT file exported from Amazon Seller Central",
        )

    try:
        raw_bytes = await file.read()
        # Decode handling UTF-8 with BOM or ISO-8859-1 fallback
        try:
            content = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw_bytes.decode("latin-1")

        result = AmazonReportSynchronizer.sync_date_range_report(
            db=db,
            org=org,
            raw_csv_content=content,
        )

        return ImportResultResponse(
            message=f"Successfully processed {result['rows_parsed']} transactions ({result['orders_imported']} new orders, {result['orders_updated']} updated, {result['fees_extracted']} fees).",
            rows_parsed=result["rows_parsed"],
            orders_imported=result["orders_imported"],
            orders_updated=result["orders_updated"],
            refunds_imported=result["refunds_imported"],
            fees_extracted=result["fees_extracted"],
            total_sales_value=result["total_sales_value"],
            skus_identified=result["skus_identified"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Amazon Date Range report: {str(e)}",
        )


@router.post("/products/cogs-csv", response_model=COGSImportResponse)
async def upload_products_cogs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """
    Upload seller product cost (COGS) CSV containing SKU, product cost, packaging cost, and other costs.
    """
    if not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file",
        )

    try:
        raw_bytes = await file.read()
        try:
            content = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw_bytes.decode("latin-1")

        result = COGSImporter.import_cogs_csv(
            db=db,
            org=org,
            csv_content=content,
        )

        return COGSImportResponse(
            message=f"Successfully updated unit costs for {result['products_updated']} products ({result['products_created']} new SKUs added).",
            rows_processed=result["rows_processed"],
            products_updated=result["products_updated"],
            products_created=result["products_created"],
            updated_skus=result["updated_skus"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process COGS CSV: {str(e)}",
        )


@router.get("/sample/{report_type}")
def get_sample_report_template(report_type: str):
    """Download clean sample templates for Amazon Date Range and Seller COGS files."""
    if report_type == "amazon_date_range":
        content = (
            "Date Range Report\n"
            "Report generated for: Apex Retail India\n\n"
            "Date/Time,Settlement id,type,Order ID,SKU,Description,Quantity,Marketplace,fulfillment,city,state,postal code,Product Sales,Product Sales Tax,Shipping Credits,Shipping Credits Tax,Gift wrap credits,Giftwrap credits tax,Regulatory Fee,Tax on Regulatory Fee,Promotional Rebates,Promotional Rebates Tax,Marketplace Withheld Tax,Selling fees,FBA fees,Other transaction fees,Other,Total\n"
            "02-Sep-2026 14:22:10 IST,182910291,Order,402-9988271-1029381,CU-BOTTLE-1000ML,Pure Copper Hammered Water Bottle 1000ml,1,amazon.in,Seller,Mumbai,Maharashtra,400001,999.00,152.38,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,-9.99,-144.88,-75.00,0.00,0.00,769.13\n"
            "03-Sep-2026 18:05:42 IST,182910291,Order,402-1102938-5928371,AUDIO-AIR-PODS-PRO,True Wireless Earbuds with ANC,1,amazon.in,Amazon,Bengaluru,Karnataka,560001,1499.00,228.66,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,-14.99,-215.85,-95.00,0.00,0.00,1173.16\n"
            "04-Sep-2026 11:15:30 IST,182910291,Order,402-3344556-7788990,KURTA-COTTON-SL-NAVY,Men Pure Cotton Navy Blue Kurta,1,amazon.in,Seller,Delhi,Delhi,110001,799.00,95.88,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,-7.99,-119.85,-65.00,0.00,0.00,606.16\n"
        )
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=amazon_india_date_range_sample.csv"},
        )
    elif report_type == "seller_cogs":
        content = (
            "sku,title,product_cost,packaging_cost,other_cost\n"
            "CU-BOTTLE-1000ML,Pure Copper Hammered Water Bottle 1000ml,350.00,20.00,10.00\n"
            "AUDIO-AIR-PODS-PRO,True Wireless Earbuds with ANC,520.00,35.00,15.00\n"
            "KURTA-COTTON-SL-NAVY,Men Pure Cotton Navy Blue Kurta,260.00,15.00,10.00\n"
            "DESK-MAT-LEATHER-BRW,Dual-Sided Waterproof Desk Mat,180.00,18.00,5.00\n"
        )
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=seller_cogs_sample.csv"},
        )
    else:
        raise HTTPException(status_code=404, detail="Unknown sample report type")
