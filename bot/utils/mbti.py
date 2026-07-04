MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

MBTI_COMPATIBILITY = {
    "INTJ": ["ENFP", "ENTP", "INFJ", "INTP"],
    "INTP": ["ENTJ", "ENFJ", "INTJ", "INFP"],
    "ENTJ": ["INTP", "INTJ", "ENFP", "ENTP"],
    "ENTP": ["INTJ", "INFJ", "INTP", "ENFP"],
    "INFJ": ["ENFP", "ENTP", "INTJ", "INFP"],
    "INFP": ["ENFJ", "ENTJ", "INFJ", "INTP"],
    "ENFJ": ["INFP", "INTP", "ENFP", "INFJ"],
    "ENFP": ["INFJ", "INTJ", "ENFJ", "ENTP"],
    "ISTJ": ["ESFP", "ESTP", "ISFJ", "ISTP"],
    "ISFJ": ["ESFP", "ESTP", "ISTJ", "ISFP"],
    "ESTJ": ["ISFP", "ISTP", "ESFJ", "ESTP"],
    "ESFJ": ["ISFP", "ISTP", "ESTJ", "ESFP"],
    "ISTP": ["ESTJ", "ESFJ", "ISTJ", "ISFJ"],
    "ISFP": ["ESTJ", "ESFJ", "ISFP", "ISTP"],
    "ESTP": ["ISFJ", "ISTJ", "ESFP", "ESTJ"],
    "ESFP": ["ISFJ", "ISTJ", "ESFJ", "ESTP"],
}


def get_compatible_types(mbti: str) -> list:
    return MBTI_COMPATIBILITY.get(mbti, [])


def is_compatible(type1: str, type2: str) -> bool:
    return type2 in get_compatible_types(type1)


def validate_mbti(mbti: str) -> bool:
    return mbti.upper() in MBTI_TYPES
