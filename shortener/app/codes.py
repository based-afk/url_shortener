ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CHARTOPOS = {}
for i in range(0,len(ALPHABET)):
    CHARTOPOS[ALPHABET[i]] = i 

BASE = len(ALPHABET)  # 62


def encode_base62(n: int) -> str:
    # TODO: the % and // loop from Step 1
    # Watch out: what happens when n == 0?
    if n<0:
        raise ValueError("n cannot be less than 0")
    if n==0:
        return ALPHABET[0]
    result = ""
    while n > 0:
        digit = n%62
        result+=ALPHABET[digit]
        n//=62
    return result[::-1]


def decode_base62(s: str) -> int | None:
    # TODO: the "result * 62 + position" loop from Step 1
    # Return None if s is empty or contains a character not in ALPHABET
    if not s :
        return None
    for ch in s :
        if ch not in ALPHABET:
            return None
    result = 0
    for ch in s :
        result = result*62 + CHARTOPOS.get(ch)
    return result

    


def id_to_code(id: int) -> str:
    return encode_base62(id)


def code_to_id(code: str) -> int | None:
    return decode_base62(code)