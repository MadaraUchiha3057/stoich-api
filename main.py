from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chempy import balance_stoichiometry, Substance

app = FastAPI(title="Chemistry Yield API")

# This is what the user sends to your API
class YieldRequest(BaseModel):
    equation: str        # Example: "H2 + O2 -> H2O"
    start_substance: str # Example: "H2"
    start_mass: float    # Example: 10.0
    target_substance: str# Example: "H2O"

@app.get("/")
def health_check():
    return {"message": "Stoichiometry API is Online"}

@app.post("/calculate")
async def calculate(data: YieldRequest):
    try:
        # 1. Separate the equation into Reactants and Products
        reac_str, prod_str = data.equation.split("->")
        reactants = [r.strip() for r in reac_str.split("+")]
        products = [p.strip() for p in prod_str.split("+")]

        # 2. Balance the equation automatically
        reac_coeff, prod_coeff = balance_stoichiometry(set(reactants), set(products))

        # 3. Get Molar Masses (Converted to standard float for FastAPI)
        molar_mass_start = float(Substance.from_formula(data.start_substance).mass)
        molar_mass_target = float(Substance.from_formula(data.target_substance).mass)

        # 4. Stoichiometry Math
        moles_start = data.start_mass / molar_mass_start
        
        # Get the ratio from the balanced equation
        ratio = float(prod_coeff[data.target_substance]) / float(reac_coeff[data.start_substance])
        
        # Theoretical Yield Calculation
        yield_mass = moles_start * ratio * molar_mass_target

        # We convert everything to standard Python types (dict, float, str)
        return {
            "status": "success",
            "balanced_equation": f"{dict(reac_coeff)} -> {dict(prod_coeff)}",
            "input": {
                "substance": data.start_substance,
                "amount": float(data.start_mass),
                "unit": "g"
            },
            "theoretical_yield": {
                "substance": data.target_substance,
                "amount": round(float(yield_mass), 4),
                "unit": "g"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Check your formula! Error: {str(e)}")