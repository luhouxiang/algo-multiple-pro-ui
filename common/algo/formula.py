

# %% 公式
# //////////////////////////////////////////////////////////////////////////////
class MA:
    def __init__(self, e0=5):
        self.e0 = e0
        self.ma, self.malist = 0, []
        self.name = f"{self.__class__.__name__}{self.e0}"

    def input(self, price):
        self.malist.append(price)
        self.malist = self.malist[-self.e0:]
        self.ma = sum(self.malist) / len(self.malist)
# //////////////////////////////////////////////////////////////////////////////