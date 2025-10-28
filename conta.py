class Conta:
    def __init__(self, numero, saldo, valor, id):
        self.numero = numero
        self.saldo = saldo
        self.valor = valor
        self.id = id

    def Saldo(self):
        saldo = self.saldo
        print(f'Seu saldo total e de:' + saldo )


    def saque(self, valor):
        saque = self.saldo - valor
        saqueefetuado = saque
        print(f'seu saldo apos o saque e de:' + saqueefetuado)


    def deposito(self,valor):
        deposito = valor + self.saldo
        print(f"Seu deposito foi efetuado com sucesso. seu saldo atual e de:"+ deposito)