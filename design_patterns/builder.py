# Builder, creational design pattern

class Computer:
    def __init__(self):
        self.cpu = None
        self.ram = None
        self.storage = None

    def set_cpu(self, cpu):
        self.cpu = cpu

    def set_ram(self, ram):
        self.ram = ram

    def set_storage(self, storage):
        self.storage = storage

    def build(self):
        return self

class ComputerBuilder:
    def __init__(self):
        self.computer = Computer()

    def set_cpu(self, cpu):
        self.computer.set_cpu(cpu)
        return self

    def set_ram(self, ram):
        self.computer.set_ram(ram)
        return self

    def set_storage(self, storage):
        self.computer.set_storage(storage)
        return self

    def build(self):
        return self.computer

# Usage
builder = ComputerBuilder()
computer = builder.set_cpu("Intel Core i7").set_ram("16GB").set_storage("1TB SSD").build()
print(computer.cpu, computer.ram, computer.storage)
print(computer)

# Benefits of using the Builder pattern in this example:
# 
# Flexibility: You can create different pizza variations by combining different components.
# Readability: The builder's fluent interface makes the code more readable and easier to understand.
# Control over the construction process: You can add components in any order you like.
