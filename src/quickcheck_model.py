



def check_capacity_vs_demand(I, J, D, C):
    errors = []
    
    for m in I:
        total_capacity = sum(C.get((m,s), 0) for s in J)
        
        if total_capacity < D[m]:
            errors.append({
                "type": "capacity_shortage",
                "item": m,
                "demand": D[m],
                "capacity": total_capacity
            })
    
    return errors

def check_leadtime_coverage(I, IDX, L, MD):
    errors = []
    
    for m in I:
        feasible_options = [
            (s,b) for (mm,s,b) in IDX
            if mm == m and L.get((m,s,b), float('inf')) <= MD[m]
        ]
        
        if len(feasible_options) == 0:
            errors.append({
                "type": "leadtime_infeasible",
                "item": m,
                "required_days": MD[m]
            })
    
    return errors
def check_index_consistency(IDX, C, L):
    errors = []
    
    for (m,s,b) in IDX:
        
        if (m,s) not in C:
            errors.append({
                "type": "missing_capacity",
                "key": (m,s)
            })
        
        if (m,s,b) not in L:
            errors.append({
                "type": "missing_leadtime",
                "key": (m,s,b)
            })
    
    return errors



#---------------


def check_revenue_vs_capacity(J, IDX, C, P, R):
    
    errors = []
    
    for s in J:

        max_spend = 0

        
        for (m,ss,b) in IDX:
            if ss != s:
                continue
            
            cap = C.get((m,s), 0)
            
            # get max price across brackets for (m,s)
            prices = [
                P[m,s,bb] for (mm,ss2,bb) in IDX
                if mm == m and ss2 == s
            ]
            
            if prices:
                max_price = max(prices)
                max_spend += cap * max_price
        
        # if max_spend < R.get(s, 0):
        errors.append({
            "type": "revenue_infeasible",
            "supplier": s,
            "required": R[s],
            "max_possible": max_spend
        })
    
    return errors


def check_revenue_vs_demand(J, IDX, D, P, R):
    errors = []
    
    for s in J:
        max_spend = 0
        
        for m in D.keys():
            prices = [
                P[m,s,b] for (mm,ss,b) in IDX
                if mm == m and ss == s
            ]
            
            if prices:
                max_price = max(prices)
                max_spend += D[m] * max_price
        
        # if max_spend < R.get(s, 0):
        errors.append({
            "type": "revenue_exceeds_demand",
            "supplier": s,
            "required": R[s],
            "max_possible": max_spend
        })
    
    return errors


def check_revenue_realistic(J, IDX, D, C, P, R):
    errors = []
    
    for s in J:
        max_spend = 0
        
        items = set([m for (m,ss,b) in IDX if ss == s])
        
        for m in items:
            cap = C.get((m,s), 0)
            demand = D.get(m, 0)
            
            effective_qty = min(cap, demand)
            
            prices = [
                P[m,s,b] for (mm,ss,b) in IDX
                if mm == m and ss == s
            ]
            
            if prices:
                max_price = max(prices)
                max_spend += effective_qty * max_price
        
        # if max_spend < R.get(s, 0):
        errors.append({
            "type": "revenue_infeasible_realistic",
            "supplier": s,
            "required": R[s],
            "max_possible": max_spend
        })
    
    return errors