import fitz
from pathlib import Path

# This function combines pdf saved with "wood" or "veg" prefix as 
# a combined pdf with "fuel" prefix

fns_veg = [f for f in sorted(Path().glob('veg*.pdf'))]
fns_wood = [f for f in sorted(Path().glob('wood*.pdf'))]

for f in fns_veg:
    for f2 in fns_wood:
        check = [str(f)[4:-4] == str(f2)[5:-4], f.exists(), f2.exists()]
        if all(check): 
            pdf1 = fitz.Document(f)
            pdf2 = fitz.Document(f2)
            pdf2.insert_pdf(pdf1)
            pdf2.save("fuel_" + str(f)[4:])
            pdf1.close()
            pdf2.close()
            f.unlink()
            f2.unlink()