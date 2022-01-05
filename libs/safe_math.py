# todo: move all methods to big_numbers.py


def div(x: int, y: int):
    return x // y

 
def sqrt(y: int):
    if (y > 3):
        z = y
        x = y // 2 + 1

        while x < z:
            z = x
            x = (y // x + x) // 2

        return z
    elif y != 0:
        z = 1

        return z

    return 0

# a library for handling binary fixed point numbers (https://en.wikipedia.org/wiki/Q_(number_format))
def q_encode(x: int):
    z = x << 112

    return z


# todo: remove 144 from name
def q_decode_144(x: int):
    if x is None:
        return None # todo: deal with this case
        
    z = x >> 112

    return z

def q_div(x: int, y: int):
    z = x // y

    return z

