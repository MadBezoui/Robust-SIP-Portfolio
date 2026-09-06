import re

with open("CITATION.cff", "r") as f:
    cff = f.read()

bounceur_str = """  - family-names: "Sifaoui"
    given-names: "Thiziri"
    orcid: "https://orcid.org/0009-0007-6884-0611"
    affiliation: "University of Amine Elokkal El Hadj Moussa Eg Akhamouk, Tamanghasset, Algeria"
  - family-names: "Bounceur"
    given-names: "Ahcene"
    orcid: "https://orcid.org/0000-0002-0043-7742"
    affiliation: "College of Computing and Informatics, University of Sharjah, United Arab Emirates\""""

cff = cff.replace("""  - family-names: "Sifaoui"
    given-names: "Thiziri"
    orcid: "https://orcid.org/0009-0007-6884-0611"
    affiliation: "University of Amine Elokkal El Hadj Moussa Eg Akhamouk, Tamanghasset, Algeria\"""", bounceur_str)

with open("CITATION.cff", "w") as f:
    f.write(cff)
