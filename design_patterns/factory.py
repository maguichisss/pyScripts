# Factory, creational design pattern

class Pizza:
    def __init__(self, ingredients):
        self.ingredients = ingredients

    def prepare(self):
        print(f"Preparing pizza with {self.ingredients}")

class CheesePizza(Pizza):
    def __init__(self):
        super().__init__(["cheese"])

class PepperoniPizza(Pizza):
    def __init__(self):
        super().__init__(["cheese", "pepperoni"])

class PizzaFactory:
    @staticmethod
    def create_pizza(pizza_type):
        if pizza_type == "cheese":
            return CheesePizza()
        elif pizza_type == "pepperoni":
            return PepperoniPizza()
        else:
            raise ValueError("Invalid pizza type")

# Usage
pizza = PizzaFactory.create_pizza("cheese")
pizza.prepare()
pizza2 = PizzaFactory.create_pizza("pepperoni")
pizza2.prepare()


# Benefits of the Factory Pattern:
# 
# Decouples the client code from the concrete classes: The client code doesn't need to know the specific class of the pizza it's creating.
# Makes the code more extensible: Adding new pizza types is easy without modifying existing code.
# Promotes code reuse: The factory can be used to create multiple instances of the same pizza type.
