class Player:

  def __init__(self):
    self.exp = 0
    self.doubloons = 0
    self.health = 100
    self.inventory = {}

  def award_exp(self, exp):
    self.exp += exp

  def get_stats(self):
    return self.exp, self.health

  def decrement_health(self, damage):
    self.health -= damage
    self.health = max(0, self.health)

  def add_to_inventory(self, category, item):
    if category not in self.inventory:
      self.inventory[category] = []
    self.inventory[category].append(item)

  def view_inventory(self):
    if not any(self.inventory.values()):
      return "Your inventory is empty."
    inventory_items = []
    for category, items in self.inventory.items():
      if items:
        items_str = [str(item) for item in items]
        inventory_items.append(
            f"{category.capitalize()}: {', '.join(items_str)}")
    return '\n'.join(inventory_items)
