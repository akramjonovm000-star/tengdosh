from utils.text_utils import format_uzbek_name

names = [
    "Navro'Z",
    "Navro'z",
    "G'Ofurov",
    "G'ofurov",
    "O'G'Li",
    "O'g'li",
    "Sa'Dullaev",
    "Sa'dullaev"
]

print(f"{'Original':<15} | {'capitalize()':<15} | {'title()':<15} | {'format_uzbek_name()':<20}")
print("-" * 70)

for n in names:
    cap = n.capitalize()
    tit = n.title()
    uz = format_uzbek_name(n)
    print(f"{n:<15} | {cap:<15} | {tit:<15} | {uz:<20}")
