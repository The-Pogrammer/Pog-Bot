import re


class expressionHandler:
    def __init__(self):
        self.Expression = ""
        self.StringList = []
        self.ExpressionList = []
        self.Variables = {}
        self.IntialState: bool = (
            True  # True = starts with expression, False = starts with string
        )

    def __str__(self) -> str:
        if self.Expression.strip() == "":
            return "None"
        return self.Expression.strip()

    #special math handler, like squares and roots
    def specialMath(self, expression: str):
        pass
    
    def solveExpressions(self):
        if self.ExpressionList == []:
            return
        exprOutputs = []

        for expression in self.ExpressionList:
            for var in self.Variables:
                expression = expression.replace(var, str(self.Variables[var]))

        try:
            expression = eval(expression)
            exprOutputs.append(expression)
        except NameError:
            # TODO Handle this
            exprOutputs.append("NaN")
            pass
        self.ExpressionList = exprOutputs

    def combineBackTogether(self, lst1, lst2):
        if not lst1:
            return lst2
        if not lst2:
            return lst1
        return [lst1[0], lst2[0]] + self.combineBackTogether(lst1[1:], lst2[1:])

    def intereptPrint(self, stringExpression: str):
        if stringExpression[0] == '"':
            self.IntialState = False

        quoted = re.findall(r'"(.+?)"', stringExpression)
        self.StringList.extend(quoted)

        outsideQuotes = re.findall(
            r'(\w+\+\w+)(?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)',
            stringExpression,
        )
        self.ExpressionList.extend([oq[0] for oq in outsideQuotes])

        self.solveExpressions()
        if self.IntialState:
            lst1 = self.ExpressionList
            lst2 = self.StringList
        else:
            lst1 = self.StringList
            lst2 = self.ExpressionList
        combined = self.combineBackTogether(lst1, lst2)
        # combine list as one string
        self.Expression += "".join(map(str, combined)) + "\n"

    def intereptVariables(self, variableExpression: str):
        matches = re.findall(":(.+?)=(\d+)", variableExpression)
        for match in matches:
            # check to make sure match[0] contains at least one letter character
            if re.search("[a-zA-Z]", match[0]):
                self.Variables[match[0]] = match[1]
            else:
                pass
                # TODO HANDLE THIS

    def intereptExpression(self, expression: str):
        cmd = expression.split(":")[0]
        inpExpr = expression.replace(cmd, "")
        if cmd == "def":
            self.intereptVariables(inpExpr)
        elif cmd == "pr":
            self.reset()
            self.intereptPrint(inpExpr[1:])
        else:
            raise Exception(f"Unknown command: {cmd}")

    def clear(self):
        self.Expression = ""

    def reset(self):
        self.StringList = []
        self.ExpressionList = []
        self.IntialState = True

    def clearVariables(self):
        self.Variables = {}


class Users:
    def __init__(self) -> None:
        self.users: dict[int, expressionHandler] = {}

    def get(self, user_id: int) -> expressionHandler:
        if user_id not in self.users:
            self.users[user_id] = expressionHandler()
        return self.users[user_id]


def main():
    handler = expressionHandler()
    input = 'pr:"hello"'
    for s in input.split(";"):
        handler.intereptExpression(s)
    print(handler.ExpressionList)
    print(handler.Variables)
    print(f"{handler}")
    handler.clear()


if __name__ == "__main__":
    main()
