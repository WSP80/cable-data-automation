let
    Quelle = (Parameter1) => let
        Quelle = Excel.Workbook(Parameter1, null, true),
        TDSheet_Sheet = Quelle{[Item="TDSheet",Kind="Sheet"]}[Data]
    in
        TDSheet_Sheet
in
    Quelle