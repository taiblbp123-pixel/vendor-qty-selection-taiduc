
import pandas as pd
import numpy as np
import re
import os


from src.config import *



# --------------------- supply (vendor-data processing) ----------------------------------------

def _melt_bracket_df(df, value_name):
    """
    Convert wide bracket format → long format
    """
    item_cols = "Item_Code" #item_code name on Excel file
    bracket_cols = [c for c in df.columns if c != item_cols]
    
    def _parse_bracket(col_name, idx):
        """
        Convert bracket column name to structured fields
        """
        col_name = str(col_name).strip()

        if "+" in col_name: #HIGHEST BRACKET
            lower = int(col_name.replace("+", ""))
            upper = BIG_M
        else:
            parts = col_name.split("-")
            lower = int(parts[0])
            upper = int(parts[1])

        return {
            "bracket_no": idx + 1,
            "lower_bound": lower,
            "upper_bound": upper
        }
    
    
    
    
    # build a long-format data from Wide-format
    unpivot_df = df.melt(
        id_vars=item_cols,
        value_vars=bracket_cols,
        var_name="bracket_range",
        value_name=value_name
    ).copy()

    # build bracket data
    bracket_map = {
        col: _parse_bracket(col, i)
        for i, col in enumerate(bracket_cols)
    }

    bracket_df = pd.DataFrame.from_dict(bracket_map, orient="index").reset_index()
    bracket_df = bracket_df.rename(columns={"index": "bracket_range"})
    
    # merge 2 table
    unpivot_df = unpivot_df.merge(bracket_df, on="bracket_range", how="left")

    return unpivot_df.rename(columns={"Item_Code": "item_code"})
    
def load_vendor_file(file_path):
    """
    Main function:
    Load + normalize 1 vendor file
    - intput: 1 files, 4 sheet (price , revenue, leadtime, capacity)
    - output: 4 df
    """
    
    # ---------- LOAD ----------
    xls = pd.ExcelFile(file_path)
    
    vendor_name = os.path.splitext(os.path.basename(file_path))[0]

    price_raw = pd.read_excel(xls, "Price")
    capacity_raw = pd.read_excel(xls, "Capacity")
    leadtime_raw = pd.read_excel(xls, "Leadtime")
    
    # revenue sheet may not exist
    if "Revenue" in xls.sheet_names:
        revenue_raw = pd.read_excel(xls, "Revenue", header=None)
    else:
        revenue_raw = None
        
    
    # ---------- TRANSFORM ----------
    
    # price
    price_df = _melt_bracket_df(price_raw, "price")
    price_df["vendor"] = vendor_name
    # lead time
    leadtime_df = _melt_bracket_df(leadtime_raw, "lead_time")
    leadtime_df["vendor"] = vendor_name
    # capacity
    capacity_df = capacity_raw.rename(columns={
        "Item_Code": "item_code",
        "Capacity": "capacity"
    })
    capacity_df["vendor"] = vendor_name
    
    # revenue 
    
    if revenue_raw is None or revenue_raw.empty:
        revenue_value = 0.0
    else: 
        val = revenue_raw.iat[0,0]
        revenue_value = 0.0 if pd.isna(val) else float(val)
    revenue_dict = {
        "vendor": vendor_name,
        "revenue": revenue_value
    }
    
    # ---------- FINAL COLUMN ORDER ----------
    
    
    price_df = price_df[[
        "vendor", "item_code",
        "bracket_no", "bracket_range",
        "lower_bound", "upper_bound",
        "price"
    ]]

    capacity_df = capacity_df[[
        "vendor", "item_code", "capacity"
    ]]


    leadtime_df = leadtime_df[[
        "vendor", "item_code",
        "bracket_no", "bracket_range",
        "lower_bound", "upper_bound",
        "lead_time"
    ]]
    
    
    xls.close()
    
    
    return price_df, capacity_df, revenue_dict, leadtime_df
#-----final task------
def load_all_vendors(folder_path):
    """
    Load and combine all vendor Excel files in a folder
    
    Output:
    - price_all
    - capacity_all
    - revenue_all
    - leadtime_all
    """
    
    # ---------- CONTAINERS ----------
    price_list = []
    capacity_list = []
    leadtime_list = []
    revenue_list = []
    
    # ---------- FILE DISCOVERY ----------
    files = [
        f for f in os.listdir(folder_path)
        if f.endswith(".xlsx") or f.endswith(".xls")
    ]
    
    if not files:
        print("[!] No vendor files found.") #raise ValueError("No Excel files found in folder")
        return
        
    # ---------- FILE PROCESSING ----------
    print(f"[OK]  Raw Supply   : {len(files)} vendors identified.")
    
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            price_df, capacity_df, revenue_dict, leadtime_df = load_vendor_file(file_path)
            
            price_list.append(price_df)
            capacity_list.append(capacity_df)
            leadtime_list.append(leadtime_df)
            revenue_list.append(revenue_dict)
            
            print(f"       [+] {file}   [DONE]")
        except Exception as e:
            print(f"       [+] {file}   [ERROR]")
            continue
    
    
    # ---------- APPENDING FINAL RESULT ----------
    
    price_all = pd.concat(price_list, ignore_index=True)
    capacity_all = pd.concat(capacity_list, ignore_index=True)
    leadtime_all = pd.concat(leadtime_list, ignore_index=True)
    
    revenue_all = pd.DataFrame(revenue_list)
    
    
    
    data = {"price" : price_all,
            "capacity" : capacity_all,
            "revenue" : revenue_all,
            "leadtime" : leadtime_all
        
    }
    return data


# --------------------- demand (productions-data processing) ----------------------------------------

def normalize_demand(df):
    df = df.copy()

    plant_cols = [c for c in df.columns if c != "Product"]

    demand_df = df.melt(
        id_vars=["Product"],
        value_vars=plant_cols,
        var_name="plant",
        value_name="demand_qty"
    )

    demand_df = demand_df.rename(columns={
        "Product": "product"
    })

    return demand_df

def normalize_bom(df):
    df = df.copy()

    item_cols = [c for c in df.columns if c != "Product"]

    bom_df = df.melt(
        id_vars=["Product"],
        value_vars=item_cols,
        var_name="item_code",
        value_name="usage_qty"
    )

    bom_df = bom_df.rename(columns={
        "Product": "product"
    })

    # remove zero usage (important)
    bom_df = bom_df[bom_df["usage_qty"] > 0]

    return bom_df


def normalize_delivery(df):
    df = df.copy()

    plant_cols = [c for c in df.columns if c != "Product"]

    delivery_df = df.melt(
        id_vars=["Product"],
        value_vars=plant_cols,
        var_name="plant",
        value_name="delivery_date"
    )

    delivery_df = delivery_df.rename(columns={
        "Product": "product"
    })

    delivery_df["delivery_date"] = pd.to_datetime(
        delivery_df["delivery_date"],
        dayfirst=True,
        errors="coerce"
    )

    return delivery_df


def explode_material_demand(demand_df, bom_df, delivery_df):
    """
    Convert product-date demand → item-date level demand
    """
    
    
    # explosion demand: product --> material
    df = demand_df.merge(
        bom_df,
        on="product",
        how="inner"
    )
    df["required_qty"] = df["demand_qty"] * df["usage_qty"]
    # attach delivery date
    
    df = df.merge(
        delivery_df,
        on=["product", "plant"],
        how="left"
    )
    
    
    
    # full_cols = ['product', 'plant', 'demand_qty', 'item_code', 'usage_qty','required_qty', 'delivery_date']
    target_cols = ['item_code','delivery_date','required_qty', 'plant']

    
    # final result
    
    return df[target_cols]


#-----final task------
def load_production_file(file_path):
    
    status = {"demand": "ERROR", "delivery": "ERROR", "bom": "ERROR"}
    final_count = 0
    
    try:
        xls = pd.ExcelFile(file_path)
        # 1. Process Demand
        demand_raw = pd.read_excel(xls, "Demand")
        demand_df = normalize_demand(demand_raw)
        status["demand"] = "DONE"
        # 2. Process Delivery
        delivery_raw = pd.read_excel(xls, "Delivery")
        delivery_df = normalize_delivery(delivery_raw)
        status["delivery"] = "DONE"
        # 3. Process BOM
        bom_raw = pd.read_excel(xls, "BOM")
        bom_df = normalize_bom(bom_raw)
        status["bom"] = "DONE"
        # 4. Explode
        
        data = explode_material_demand(demand_df, bom_df, delivery_df)
        final_count = len(data)
        
        xls.close()
        
    except Exception as e:
            print(f"\n[!] CRITICAL ERROR at Raw Demand: {e}")
            # data remains undefined or empty here
            data = pd.DataFrame()
        
    # --------- FINAL PRINT OUT ----------
    print(f"[OK]  Raw Demand   : {final_count:,} records loaded.")
    print(f"       [+] sheet demand   [{status['demand']}]")
    print(f"       [+] sheet delivery [{status['delivery']}]")
    print(f"       [+] sheet bom      [{status['bom']}]")
    
    return data
