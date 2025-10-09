import crypt_lib as cl
import math
import random


def baby_step_giant_step(a, y, p):
    """
    Решает задачу дискретного логарифма методом "Шаг младенца, шаг великана".

    Находит такое значение x, что удовлетворяет уравнению y = a^x mod p.
    Алгоритм основан на идее "встречи посередине" и имеет временную
    сложность O(sqrt(p)), что значительно эффективнее полного перебора.
    
    Args:
        a (int): Основание степени.
        y (int): Результат возведения в степень по модулю.
        p (int): Простой модуль.
        
    Returns:
        int or None: Целое число x, являющееся решением уравнения.
                     Возвращает None, если решение не найдено.
    """

    m = int(math.sqrt(p)) + 1

    baby_steps = {}
    val = 1
    for j in range(m):
        baby_steps[val] = j
        val = (val * a) % p

    a_inv_m = cl.mod_inverse(cl.fast_exp_mod(a, m, p), p)

    giant_step_val = y
    for i in range(m):
        if giant_step_val in baby_steps:
            j = baby_steps[giant_step_val]
            return i * m + j
        giant_step_val = (giant_step_val * a_inv_m) % p

    return None



def get_bsgs_input_from_keyboard():
    """
    Получение параметров a, y, p с клавиатуры.
    """
    try:
        p = int(input("Введите простой модуль p: "))
        if not cl.fermat_primality_test(p):
            print(f"Предупреждение: {p} не является вероятно простым числом.")
        a = int(input(f"Введите основание a (1 < a < {p-1}): "))
        y = int(input(f"Введите результат y (1 < y < {p-1}): "))
        return a, y, p
    except ValueError:
        print("Ошибка: введите целые числа!")
        return None, None, None



def generate_bsgs_parameters(min_p=100000, max_p=10000000):
    """
    Генерация параметров a, y, p для задачи дискретного логарифма.
    """
    print("Генерация параметров...")
    p = 0
    while True:
        num = random.randint(min_p, max_p)
        if cl.fermat_primality_test(num):
            p = num
            break
            
    a = random.randint(2, p - 2)
    x_true = random.randint(2, p - 2)
    y = cl.fast_exp_mod(a, x_true, p)
    
    print(f"Сгенерированы следующие параметры:")
    print(f"p = {p}")
    print(f"a = {a}")
    print(f"y = {y}")
    print(f"(Для проверки: секретный x был равен {x_true})")
    
    return a, y, p
    


def demo_bsgs():
    while True:
        print("\n" + "=" * 50)
        print("Алгоритм 'Шаг младенца, шаг великана'")
        print("Найти x в уравнении y = a^x mod p")
        print("=" * 50)
        print("1 - Ввод a, y, p с клавиатуры")
        print("2 - Сгенерировать a, y, p автоматически")
        print("0 - Вернуться в главное меню")
        
        choice = input("Ваш выбор: ")

        if choice == '0':
            break
        
        a, y, p = None, None, None
        
        if choice == '1':
            a, y, p = get_bsgs_input_from_keyboard()
        elif choice == '2':
            a, y, p = generate_bsgs_parameters()
        else:
            print("Неверный выбор!")
            continue

        if a is not None:
            print("\nВычисление x...")
            x = baby_step_giant_step(a, y, p)
            
            if x is not None:
                print(f"\n>>> РЕШЕНИЕ НАЙДЕНО: x = {x}")
                check = cl.fast_exp_mod(a, x, p) 
                print(f"Проверка: {a}^{x} mod {p} = {check}")
                if check == y:
                    print("Проверка пройдена успешно!")
                else:
                    print("ВНИМАНИЕ: Проверка не пройдена!")
            else:
                print("\n>>> Решение не найдено.")
