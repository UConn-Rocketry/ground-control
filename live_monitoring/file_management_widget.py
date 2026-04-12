from PySide6 import QtWidgets
from pathlib import Path
from os import mkdir, path
from shutil import rmtree



class file_management_widget(QtWidgets.QWidget):
    def __init__(self, output) -> None:
        super().__init__()
        self.layout = QtWidgets.QFormLayout(self)

        select_struct_button = QtWidgets.QPushButton("Select Struct Definition Directory")
        self.manual_struct_string = QtWidgets.QLineEdit()
        self.manual_struct_string.setPlaceholderText("Struct String")

        self.layout.addRow(select_struct_button, self.manual_struct_string)

        select_output_directory_button = QtWidgets.QPushButton("Select Output Directory")
        self.show_output_directory = QtWidgets.QLineEdit()
        self.show_output_directory.setReadOnly(True)

        self.layout.addRow(select_output_directory_button, self.show_output_directory)
        
        self.port_input = QtWidgets.QLineEdit()
        self.port_input.setPlaceholderText("Enter Port")
        self.layout.addRow(self.port_input)

        self.output = output

        self.output_location = None
        self.header = None

        self._set_to_default()

        select_output_directory_button.clicked.connect(self._get_output_location)

    def _set_to_default(self):
        self.output_directory = Path(__file__).parent.parent.joinpath("./runs").absolute()
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.find_next_available_save_location_in_current_directory()



    
    def _get_output_location(self):
        self.output_directory = Path(QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Output Location"))

        if(not self.output_directory):
            return
        self.find_next_available_save_location_in_current_directory()

    def find_next_available_save_location_in_current_directory(self):
        temp_location = self.output_directory.joinpath('./run0')
        index = 1

        while(temp_location.exists()):
            temp_location = self.output_directory.joinpath('./run'+str(index))
            index += 1
        
        self.output_location = temp_location
        self.show_output_directory.setText(str(self.output_location))


    def create_files(self):
        mkdir(self.output_location)
        mkdir(self.output_location.joinpath('./Graphs'))

        data_path = self.output_location.joinpath('./data.csv')
        log_path = self.output_location.joinpath('./output.log')

        with open(data_path, 'w') as file:
            if(self.header):
                file.write(self.header)
                file.write('\n')

        return data_path, log_path

    #Checks that data management values are valid
    def check_ready(self):
        if(not (self.output_location)):
            self.output('Error: Output Location must be set')
            return False
        elif(not self.output_location):
            self.output('Error: Must set Output Location')
            return False

        return True

    def delete_files_from_current_run(self):
        rmtree(self.output_location)

    

    
