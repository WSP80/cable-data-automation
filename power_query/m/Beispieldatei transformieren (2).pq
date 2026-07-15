let
    Quelle = Excel.Workbook(Parameter2, null, true),
    TDSheet1 = Quelle{[Name="TDSheet"]}[Data]
in
    TDSheet1