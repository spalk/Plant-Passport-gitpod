
import io
from django.templatetags.static import static
from pylibdmtx.pylibdmtx import encode
import PIL
from PIL import Image
from fpdf import FPDF

DATA_MATRIX_SIZE = 30   # px
LABEL_LENGHT = 80       # mm
VERTICAL_SPACE = 20     # mm


class Label:
    def __init__(self):
        self.puid = None
        self.dmtx = None
        self.field_number = None
        self.genus = None
        self.species = None
        self.subspecies = None
        self.variety = None
        self.cultivar = None
        self.affinity = None
        self.ex = None
        self.text_lines = []
        self.ppmm = 2.7                                             # pixels per mm
        self.dmtx_side_px = DATA_MATRIX_SIZE                        # assumed that dmtx is square and sides are euqal
        self.dmtx_side_mm = DATA_MATRIX_SIZE // self.ppmm
        self.full_length = LABEL_LENGHT

    def extract_data(self, rich_plant):
        """Fill current object with data from RichPlant"""
        self.puid =         rich_plant.uid
        self.field_number = rich_plant.attrs.number.upper()                 if rich_plant.attrs.number else None
        
        # Line 1 data
        self.genus =        rich_plant.attrs.genus.capitalize()[0] + '.'    if rich_plant.attrs.genus else None
        self.species =      rich_plant.attrs.species.lower()                if rich_plant.attrs.species else None
        self.subspecies =   rich_plant.attrs.subspecies.lower()             if rich_plant.attrs.subspecies else None
        
        # Line 2 data
        self.variety =      rich_plant.attrs.variety.lower()                if rich_plant.attrs.variety else None
        self.cultivar =     rich_plant.attrs.cultivar.title()               if rich_plant.attrs.cultivar else None

        # Line 3 data
        self.affinity =     rich_plant.attrs.affinity.title()               if rich_plant.attrs.affinity else None
        self.ex =           rich_plant.attrs.ex.title()                     if rich_plant.attrs.ex else None

        self._generate_text_lines()
        self._generate_datamatrix()

    def get_lines_number(self):
        """Returns number of text lines in label"""
        return len(self.text_lines)

    def get_width(self):
        return self.dmtx_side_px

    def _generate_text_lines(self):
        """Generating text lines according to data"""
        # Line 1 generating
        if self.genus and self.species and self.subspecies:
            text_line_1 = f'{self.genus[0]}. {self.species}  ssp. {self.subspecies}'
        else:
            text_line_1 = ''
            text_line_1 += f'{self.genus} ' if self.genus else ''
            text_line_1 += f'{self.species} ' if self.species else ''
            text_line_1 += f'ssp. {self.subspecies} ' if self.species else ''
        if text_line_1: 
            self.text_lines.append(text_line_1)

        # Line 2 generating
        text_line_2 = ''
        text_line_2 += f'v. {self.variety} ' if self.variety else ''
        text_line_2 += f'cv. {self.cultivar} ' if self.cultivar else ''
        if text_line_2: 
            self.text_lines.append(text_line_2)

        # Line 3 generating
        text_line_3 = ''
        text_line_3 += f'aff. {self.affinity} ' if self.affinity else ''
        text_line_3 += f'ex. {self.ex} ' if self.ex else ''
        if text_line_3:
            self.text_lines.append(text_line_3)

        #
        if len(self.text_lines) == 0:
            self.text_lines.append('empty')



    def _generate_datamatrix(self):
        """Data matrix image generating"""
        encoded = encode(self.puid.encode('ASCII'))
        dmtx_img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)                  # Image size is 70x70 px, where margins are 10px
        dmtx_img = dmtx_img.crop((10, 10 , 60, 60))                                                         # Crop white margins. Resulting image size is: 50x50 px
        dmtx_img = dmtx_img.resize((self.dmtx_side_px, self.dmtx_side_px), resample=PIL.Image.LANCZOS)      # Resize to IMG_WIDTH square. Think what TODO when this matrix-size will exhaust
        self.dmtx = dmtx_img


class LabelsBuilder:
    def __init__(self, rich_plants:list):
        self.rich_plants = rich_plants
        self.page_high = 297                                    # high of A4 
        self.v_space = VERTICAL_SPACE                           # vertical space between labels
        self.start_x = 10                                       # x of origin
        self.start_y = 10                                       # y of origin 
        self.column_shift = 90
        self.show_brd = 0                                       # showing of borders in cells for debugging
        self.field_num_cell_width = 6
        self.pdf = self._create_pdf()
        self.cur_x = self.start_x
        self.cur_y = self.start_y
        self.cur_lable_num = 0
        self.cur_column = 1

    def _create_pdf(self) -> FPDF:
        """PDF-object create and setup"""
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu_regular', fname='static/DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font('DejaVu_regular', size=10)
        return pdf

    def _get_start_y_position(self, label:Label):
        """Y-position calculation for current label"""
        label_heigh = label.get_width()
        v_space_left = self.page_high - self.cur_y              # free space left in the bottom of the page
        if not v_space_left - label_heigh > 10:
            self.cur_y = self.start_y
            if self.cur_column == 2:
                self.pdf.add_page()
                self.cur_column = 1
            else:
                self.cur_column = 2
        else:
            if self.cur_column == 1:
                self.cur_x = self.start_x
            elif self.cur_column == 2:
                self.cru_x = self.start_x + self.column_shift

    def _xy_update(self, shift_x=0, shift_y=0):
        """
            Updating position with current x,y values
            Additional shift is possible
        """
        self.pdf.set_xy(self.cur_x + shift_x, self.cur_y + shift_y)

    def _place_dmtx(self, label:Label):
        """Placing data matrix image"""
        self._xy_update()
        self.pdf.image(label.dmtx, x=self.cur_x, y=self.cur_y)
        self.cur_x += label.dmtx_side_mm

    def _place_frame(self, label:Label):
        """Placing frame around all label (except data matrix)"""
        horiz_shift = 1                                         # space between data matrix and frame
        self._xy_update(shift_x=horiz_shift)
        frame_heigh = label.dmtx_side_mm                        # high of label is equal to size of data matrix
        frame_width = label.full_length - label.dmtx_side_mm 
        self.pdf.cell(frame_width, frame_heigh, '', border=1)
        
    def _place_field_number(self, label:Label):
        """Placing rotaded field number"""
        self.cur_y += label.dmtx_side_mm
        self._xy_update()
        self.pdf.set_font_size(8)
        heigh = label.dmtx_side_mm                              # high of field number cell is equal to size of data matrix
        width = self.field_num_cell_width
        text = label.field_number if label.field_number else ''
        with self.pdf.rotation(90):
            self.pdf.cell(heigh, width, text, border=self.show_brd, align="C")

    def _place_text_lines(self, label:Label):
        """Placing text lines"""
        if not label.get_lines_number == 0:
            print(f'*** Label UID: {label.puid}, number of lines: {label.get_lines_number()}')
            self.cur_x += self.field_num_cell_width
            self.cur_y -= label.dmtx_side_mm
            self._xy_update()

            self.pdf.set_font_size(8)
            heigh = label.dmtx_side_mm / label.get_lines_number()
            width = label.full_length - label.dmtx_side_mm - self.field_num_cell_width

            for text in label.text_lines:
                self.pdf.cell(width, heigh, text, border=self.show_brd)
                self.cur_y += heigh
                self._xy_update()

    def generate_labels(self):
        """Generate list of Labels objects"""
        for rp in self.rich_plants:
            self.cur_lable_num += 1 
            label = Label()
            label.extract_data(rp)
            self._get_start_y_position(label)

            self._place_dmtx(label)
            self._place_frame(label)
            self._place_field_number(label)
            self._place_text_lines(label)

            self.cur_x = self.pdf.get_x()
            self.cur_y = self.pdf.get_y() + self.v_space

    def get_pdf(self):
        filename = 'pdf-dmtx-test.pdf'
        self.pdf.output(filename, 'F')
        return filename
