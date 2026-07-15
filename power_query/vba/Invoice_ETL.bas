Option Explicit

Private PipelineRunning As Boolean

Private Const CONTROL_SHEET As String = "Control"
Private Const OUTPUT_FOLDER_DISPLAY As String = "data\processed\"
Private Const BUTTON_NAME As String = "btnETL"
Private Const LOG_START_ROW As Long = 25
Private Const LOG_CLEAR_RANGE As String = "B25:B60"

Sub ExportGroupedPowerQueriesToCSV()

    Dim outputFolder As String
    Dim groups As Object
    Dim q As WorkbookQuery
    Dim qName As String
    Dim prefix As String
    Dim key As Variant
    Dim logRow As Long

    On Error GoTo ErrorHandler

    If PipelineRunning Then
        MsgBox "ETL pipeline is already running.", vbExclamation
        Exit Sub
    End If

    PipelineRunning = True

    outputFolder = CreateObject("Scripting.FileSystemObject") _
        .GetAbsolutePathName(ThisWorkbook.Path & "\..\" & OUTPUT_FOLDER_DISPLAY) & "\"

    Application.DisplayAlerts = False
    Application.StatusBar = "ETL pipeline is running..."
    Application.ScreenUpdating = True

    logRow = LOG_START_ROW

    PrepareControlPanel
    SetStatusRunning
    SetButtonRunning

    WriteLog "Starting ETL pipeline...", logRow

    If Dir(outputFolder, vbDirectory) = "" Then
        MkDir outputFolder
    End If

    WriteLog "Cleaning output folder...", logRow
    ClearOutputFolder outputFolder
    WriteLog "Output folder cleaned.", logRow

    WriteLog "Refreshing Power Query queries...", logRow

    ThisWorkbook.RefreshAll
    Application.CalculateUntilAsyncQueriesDone

    WriteLog "Power Query refresh completed.", logRow

    Set groups = CreateObject("Scripting.Dictionary")

    For Each q In ThisWorkbook.Queries

        qName = q.Name

        If IsExportQuery(qName) Then

            prefix = GetQueryPrefix(qName)

            If Not groups.Exists(prefix) Then
                groups.Add prefix, New Collection
            End If

            groups(prefix).Add qName

        End If

    Next q

    If groups.Count = 0 Then
        WriteLog "No export queries found.", logRow
        GoTo CleanExit
    End If

    For Each key In groups.Keys

        WriteLog "Exporting " & key & ".csv ...", logRow
    
        If ExportQueryGroup(groups(key), outputFolder & key & ".csv") Then
            WriteLog key & ".csv exported.", logRow
        Else
            WriteLog key & ".csv skipped: no data rows.", logRow
        End If

    Next key

    WriteLog "CSV export completed.", logRow
    WriteLog "Output folder: " & OUTPUT_FOLDER_DISPLAY, logRow

    SetStatusCompleted
    SetButtonCompleted
    RepaintControlPanel

    WaitWithDoEvents 2

CleanExit:

    Application.StatusBar = False
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True

    SetButtonReady
    RepaintControlPanel

    PipelineRunning = False

    Exit Sub

ErrorHandler:

    WriteLog "ERROR: " & Err.Description, logRow
    SetStatusError

    Application.StatusBar = False
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True

    SetButtonReady
    RepaintControlPanel

    PipelineRunning = False

    MsgBox "ETL pipeline failed: " & Err.Description, vbCritical

End Sub


Private Sub PrepareControlPanel()

    With ThisWorkbook.Worksheets(CONTROL_SHEET)
        .Range(LOG_CLEAR_RANGE).ClearContents
        .Range("C15").value = Now
        .Range("C16").value = OUTPUT_FOLDER_DISPLAY
    End With

    RepaintControlPanel

End Sub


Private Sub WriteLog(ByVal text As String, ByRef logRow As Long)

    With ThisWorkbook.Worksheets(CONTROL_SHEET)
        .Range("B" & logRow).value = Format(Now, "hh:mm:ss") & "  " & text
    End With

    logRow = logRow + 1

    RepaintControlPanel

End Sub


Private Sub RepaintControlPanel()

    Application.ScreenUpdating = True
    ThisWorkbook.Worksheets(CONTROL_SHEET).Activate
    ThisWorkbook.Worksheets(CONTROL_SHEET).Range("C14").Select
    DoEvents

End Sub


Private Sub WaitWithDoEvents(ByVal seconds As Double)

    Dim endTime As Double

    endTime = Timer + seconds

    Do While Timer < endTime
        DoEvents
    Loop

End Sub


Private Sub ClearOutputFolder(ByVal folderPath As String)

    Dim fileName As String

    fileName = Dir(folderPath & "*.csv")

    Do While fileName <> ""

        Kill folderPath & fileName

        fileName = Dir()

    Loop

End Sub


Private Sub SetStatusRunning()

    With ThisWorkbook.Worksheets(CONTROL_SHEET).Range("C14")
        .value = "Running..."
        .Interior.Color = RGB(255, 235, 156)
        .Font.Color = RGB(156, 101, 0)
    End With

    RepaintControlPanel

End Sub


Private Sub SetStatusCompleted()

    With ThisWorkbook.Worksheets(CONTROL_SHEET).Range("C14")
        .value = "Completed"
        .Interior.Color = RGB(198, 239, 206)
        .Font.Color = RGB(0, 97, 0)
    End With

    ThisWorkbook.Worksheets(CONTROL_SHEET).Range("C15").value = Now

    RepaintControlPanel

End Sub


Private Sub SetStatusError()

    With ThisWorkbook.Worksheets(CONTROL_SHEET).Range("C14")
        .value = "Error"
        .Interior.Color = RGB(255, 199, 206)
        .Font.Color = RGB(156, 0, 6)
    End With

    ThisWorkbook.Worksheets(CONTROL_SHEET).Range("C15").value = Now

    RepaintControlPanel

End Sub


Private Sub SetButtonRunning()

    On Error Resume Next

    With ThisWorkbook.Worksheets(CONTROL_SHEET).Shapes(BUTTON_NAME)
        .TextFrame.Characters.text = "Running..."
        .OnAction = ""
    End With

    RepaintControlPanel

    On Error GoTo 0

End Sub


Private Sub SetButtonReady()

    On Error Resume Next

    With ThisWorkbook.Worksheets(CONTROL_SHEET).Shapes(BUTTON_NAME)
        .TextFrame.Characters.text = "Run ETL Pipeline"
        .OnAction = "ExportGroupedPowerQueriesToCSV"
    End With

    RepaintControlPanel

    On Error GoTo 0

End Sub


Private Sub SetButtonCompleted()

    On Error Resume Next

    With ThisWorkbook.Worksheets(CONTROL_SHEET).Shapes(BUTTON_NAME)
        .TextFrame.Characters.text = "Completed"
        .OnAction = ""
    End With

    RepaintControlPanel

    On Error GoTo 0

End Sub


Private Function IsExportQuery(ByVal queryName As String) As Boolean

    Dim pos As Long
    Dim leftPart As String
    Dim rightPart As String

    pos = InStrRev(queryName, "_")

    If pos = 0 Then
        IsExportQuery = False
        Exit Function
    End If

    leftPart = Left(queryName, pos - 1)
    rightPart = Mid(queryName, pos + 1)

    IsExportQuery = Len(leftPart) > 0 And Len(rightPart) > 0

End Function


Private Function GetQueryPrefix(ByVal queryName As String) As String

    GetQueryPrefix = Left(queryName, InStrRev(queryName, "_") - 1)

End Function


Private Function ExportQueryGroup( _
    ByVal queryNames As Collection, _
    ByVal csvPath As String _
) As Boolean

    Dim stream As Object
    Dim i As Long
    Dim qName As String
    Dim tempWs As Worksheet
    Dim lo As ListObject
    Dim r As Long
    Dim c As Long
    Dim lineText As String
    Dim headerWritten As Boolean
    Dim dataWritten As Boolean
    Dim previousSheet As Worksheet

    Dim errorNumber As Long
    Dim errorDescription As String

    On Error GoTo ErrorHandler

    Set previousSheet = ThisWorkbook.Worksheets(CONTROL_SHEET)

    Application.ScreenUpdating = False

    Set stream = CreateObject("ADODB.Stream")
    stream.Type = 2
    stream.Charset = "utf-8"
    stream.Open

    headerWritten = False
    dataWritten = False

    For i = 1 To queryNames.Count

        qName = queryNames(i)

        Set tempWs = ThisWorkbook.Worksheets.Add( _
            After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count) _
        )
        tempWs.Name = GetTempSheetName()

        Set lo = LoadPowerQueryToTempTable(qName, tempWs)

        If Not lo Is Nothing Then
            If Not lo.DataBodyRange Is Nothing Then

                If Not headerWritten Then

                    lineText = ""

                    For c = 1 To lo.HeaderRowRange.Columns.Count

                        lineText = lineText & _
                            CsvEscape(lo.HeaderRowRange.Cells(1, c).value)

                        If c < lo.HeaderRowRange.Columns.Count Then
                            lineText = lineText & ";"
                        End If

                    Next c

                    stream.WriteText lineText & vbCrLf
                    headerWritten = True

                End If

                For r = 1 To lo.DataBodyRange.Rows.Count

                    lineText = ""

                    For c = 1 To lo.DataBodyRange.Columns.Count

                        lineText = lineText & _
                            CsvEscape(lo.DataBodyRange.Cells(r, c).value)

                        If c < lo.DataBodyRange.Columns.Count Then
                            lineText = lineText & ";"
                        End If

                    Next c

                    stream.WriteText lineText & vbCrLf
                    dataWritten = True

                Next r

            End If
        End If

        tempWs.Delete
        Set tempWs = Nothing
        Set lo = Nothing

    Next i

    If dataWritten Then
        stream.SaveToFile csvPath, 2
    End If

    stream.Close
    Set stream = Nothing

    previousSheet.Activate
    Application.ScreenUpdating = True
    DoEvents

    ExportQueryGroup = dataWritten
    Exit Function

ErrorHandler:

    errorNumber = Err.Number
    errorDescription = Err.Description

    On Error Resume Next

    If Not tempWs Is Nothing Then
        tempWs.Delete
    End If

    If Not stream Is Nothing Then
        stream.Close
    End If

    previousSheet.Activate
    Application.ScreenUpdating = True

    On Error GoTo 0

    Err.Raise errorNumber, "ExportQueryGroup", errorDescription

End Function

Private Function LoadPowerQueryToTempTable(ByVal queryName As String, ByVal ws As Worksheet) As ListObject

    On Error GoTo ErrorHandler

    Dim lo As ListObject

    Set lo = ws.ListObjects.Add( _
        SourceType:=0, _
        Source:="OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location=" & queryName & ";Extended Properties=""""", _
        Destination:=ws.Range("A1") _
    )

    lo.QueryTable.CommandType = xlCmdSql
    lo.QueryTable.CommandText = "SELECT * FROM [" & queryName & "]"
    lo.QueryTable.Refresh BackgroundQuery:=False

    Set LoadPowerQueryToTempTable = lo
    Exit Function

ErrorHandler:

    Set LoadPowerQueryToTempTable = Nothing

End Function


Private Function CsvEscape(ByVal value As Variant) As String

    Dim textValue As String

    If IsNull(value) Or IsEmpty(value) Then
        CsvEscape = ""
        Exit Function
    End If

    If IsDate(value) Then
        textValue = Format$(value, "yyyy-mm-dd")
    Else
        textValue = CStr(value)
    End If

    textValue = Replace(textValue, """", """""")

    CsvEscape = """" & textValue & """"

End Function


Private Function GetTempSheetName() As String

    GetTempSheetName = "tmp_export_" & Format(Now, "hhmmss") & "_" & Format(Timer * 1000, "0")

End Function

