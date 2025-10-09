import random
import crypt_lib as cl
import os
import math

import bsgs
import diffie_hellman
import shamir
import elgamal
import rsa
import vernam
import rsa_sign

def main():
    """Главное меню программы."""
    while True:
        print("\n" + "#" * 50)
        print("Криптографическая библиотека: Главное меню")
        print("#" * 50)
        print("1 - Дискретный логарифм ('Шаг младенца, шаг великана')")
        print("2 - Обмен ключами Диффи-Хеллмана")
        print("3 - Шифр Шамира")
        print("4 - Шифр Эль-Гамаля")
        print("5 - Шифр RSA")
        print("6 - Шифр Вернама")
        print("7 - Подпись/Проверка RSA")
        print("0 - Выход")

        choice = input("Ваш выбор: ")

        if choice == '0':
            print("Выход из программы.")
            break
        elif choice == '1':
            bsgs.demo_bsgs()
        elif choice == '2':
            diffie_hellman.demo_diffie_hellman()
        elif choice == '3':
            shamir.demo_shamir()
        elif choice == '4':
            elgamal.demo_elgamal()
        elif choice == '5':
            rsa.demo_rsa()
        elif choice == '6':
            vernam.demo_vernam()
        elif choice == '7':
            rsa_sign.demo_rsa_sign()
        else:
            print("Неверный выбор!")


if __name__ == "__main__":
    main()
