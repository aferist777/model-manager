"""Random English character names, gender-aware (used by the rnd button)."""

import random

FEMALE_FIRST = [
    "Mia", "Emma", "Olivia", "Ava", "Sophia", "Isabella", "Charlotte", "Amelia",
    "Harper", "Evelyn", "Aria", "Luna", "Chloe", "Zoe", "Nora", "Lily", "Ella",
    "Aurora", "Scarlett", "Ruby", "Ivy", "Hazel", "Violet", "Stella", "Nova",
    "Kira", "Maya", "Elena", "Sienna", "Willow",
]

MALE_FIRST = [
    "Liam", "Noah", "Ethan", "Mason", "Logan", "Lucas", "Jackson", "Aiden",
    "Caleb", "Ryan", "Nathan", "Dylan", "Leo", "Julian", "Adrian", "Miles",
    "Owen", "Felix", "Jasper", "Theo", "Alex", "Roman", "Elias", "Damien", "Kai",
]

LAST = [
    "Vance", "Snow", "Reyes", "Kim", "Hart", "Blake", "Stone", "Rivers", "Cole",
    "Frost", "Wells", "Lane", "Reed", "Cross", "Vaughn", "Quinn", "Sloane",
    "Monroe", "Sterling", "Bishop", "Fox", "Wilde", "Rhodes", "Cruz", "Hayes",
    "Brooks", "Ellis", "Grant", "Pierce", "Marsh", "Nash", "Sage", "Wren", "Lux",
]


def random_name(gender: str = "Female") -> str:
    if gender == "Male":
        first = random.choice(MALE_FIRST)
    elif gender == "Androgynous":
        first = random.choice(FEMALE_FIRST + MALE_FIRST)
    else:
        first = random.choice(FEMALE_FIRST)
    return f"{first} {random.choice(LAST)}"
