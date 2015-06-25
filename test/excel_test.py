#!/usr/bin/python
import xlwt
import xlrd

def create_sheet():
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet1")
    sheet2 = book.add_sheet("Sheet2")
    sheet3 = book.add_sheet("Sheet3")

    sheet1.write(0, 0, "This is the First Cell of the First Sheet")
    sheet2.write(0, 0, "This is the First Cell of the Second Sheet")
    sheet3.write(0, 0, "This is the First Cell of the Third Sheet")

    sheet2.write(1, 10, "This is written to the Second Sheet")

    sheet3.write(0, 2, "This is part of a list of information in the Third Sheet")
    sheet3.write(1, 2, "This is part of a list of information in the Third Sheet")
    sheet3.write(2, 2, "This is part of a list of information in the Third Sheet")
    sheet3.write(3, 2, "This is part of a list of information in the Third Sheet")

    book.save("python_spreadsheet.xls")


def read_sheet():
    workbook = xlrd.open_workbook("python_spreadsheet.xls")
    print workbook.sheet_names()
    sheets = workbook.sheet_names()
    worksheet = workbook.sheet_by_name(sheets[0])
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = -1
    while curr_row < num_rows:
	curr_row += 1
	row = worksheet.row(curr_row)
	print 'Row:', curr_row
	curr_cell = -1
	while curr_cell < num_cells:
		curr_cell += 1
		# Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
		cell_type = worksheet.cell_type(curr_row, curr_cell)
		cell_value = worksheet.cell_value(curr_row, curr_cell)
		print '	', cell_type, ':', cell_value

# create_sheet()
read_sheet()
