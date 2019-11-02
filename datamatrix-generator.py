#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

import pcbnew
import FootprintWizardBase

# Additional imports for DataMatrix
from hubarcode.datamatrix import DataMatrixEncoder


class DataMatrixWizard(FootprintWizardBase.FootprintWizard):
    GetName = lambda self: '2D DataMatrix'
    GetDescription = lambda self: 'DataMatrix'
    GetReferencePrefix = lambda self: 'Barcode'
    GetValue = lambda self: self.module.Value().GetText()

    def GenerateParameterList(self):
        # This should be a drop-down, allowing choice of barcode style:
        self.AddParam("Barcode", "Data Matrix", self.uBool, True)
        self.AddParam("Barcode", "Pixel Width", self.uMM, 0.5)
        self.AddParam("Barcode", "Border", self.uInteger, 0)
        self.AddParam("Barcode", "Contents", self.uString, 'DataMatrix example')
        #TODO: Add drop-down for error correction level:
        # self.AddParam("Barcode", "Error correction level", self.uString, 'L')
        self.AddParam("Barcode", "Negative", self.uBool, False)
        self.AddParam("Barcode", "Use SilkS layer", self.uBool, False)
        self.AddParam("Barcode", "Use Cu layer", self.uBool, True)
        self.AddParam("Caption", "Enabled", self.uBool, True)
        self.AddParam("Caption", "Height", self.uMM, 1.2)
        self.AddParam("Caption", "Thickness", self.uMM, 0.12)


    # def CheckParameters(self):
    #     self.useDataMatrix = self.parameters['Barcode']['*Data Matrix'] == "True"
    #     self.Barcode = str(self.parameters['Barcode']['*Contents'])
    #     self.X = self.parameters['Barcode']['Pixel Width']
    #     self.negative = self.parameters['Barcode']['*Negative'] == "True"
    #     self.UseSilkS = self.parameters['Barcode']['*Use SilkS layer'] == "True"
    #     self.UseCu = self.parameters['Barcode']['*Use Cu layer'] == "True"
    #     self.border = int(self.parameters['Barcode']['*Border'])
    #     self.textHeight = int(self.parameters['Caption']['Height'])
    #     self.module.Value().SetText(str(self.Barcode) )

    def CheckParameters(self):
        self.useDataMatrix = self.parameters['Barcode'][
            'Data Matrix']
        self.Barcode = str(self.parameters['Barcode']['Contents'])
        self.X = self.parameters['Barcode']['Pixel Width']
        self.negative = self.parameters['Barcode']['Negative']
        self.UseSilkS = self.parameters['Barcode']['Use SilkS layer']
        self.UseCu = self.parameters['Barcode']['Use Cu layer']
        self.border = int(self.parameters['Barcode']['Border'])
        self.textHeight = int(self.parameters['Caption']['Height'])
        self.module.Value().SetText(str(self.Barcode))
        self.dataMatrix = DataMatrixEncoder(str(self.Barcode)).matrix

    def _drawPixel(self, xposition, yposition):
        # build a rectangular pad: as a dot
        pad = pcbnew.D_PAD(self.module)
        pad.SetSize(pcbnew.wxSize(self.X, self.X))
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        layerset = pcbnew.LSET()
        if self.UseCu:
            layerset.AddLayer(pcbnew.F_Cu)
        if self.UseSilkS:
            layerset.AddLayer(pcbnew.F_SilkS)
        pad.SetLayerSet( layerset )
        pad.SetLocalSolderMaskMargin( -1 )
        pad.SetPosition(pcbnew.wxPoint(xposition,yposition))
        pad.SetPadName("")
        self.module.Add(pad)

    def _drawSolderMaskOpening(self, sizex, sizey, radius):
        # Draw the solder mask opening
        pad = pcbnew.D_PAD(self.module)
        pad.SetSize(pcbnew.wxSize(sizex, sizey))
        #TODO: Add fancy radius, once I figure out where to set the radius...
        # pad.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        layerset = pcbnew.LSET()
        layerset.AddLayer(pcbnew.F_Mask)
        pad.SetLayerSet( layerset )
        pad.SetLocalSolderMaskMargin( -1 )
        pad.SetPosition(pcbnew.wxPoint(0, 0))
        pad.SetPadName("")
        self.module.Add(pad)


    def BuildThisFootprint(self):
        if self.useDataMatrix:

            dataSize = len(self.dataMatrix)
            half_number_of_elements = dataSize / 2

            border_neg = -1 * self.X * (0.5 + half_number_of_elements)
            border_pos = self.X * (0.5 + half_number_of_elements)

            # First draw the standard frame:
            for x in range(-1, dataSize + 1):
                if x % 2 == 1:
                    self._drawPixel((0.5 + x - half_number_of_elements) * self.X, border_neg)
                self._drawPixel((0.5 + x - half_number_of_elements) * self.X, border_pos)

            for y in range(-1, dataSize + 1):
                self._drawPixel(border_neg, (0.5 + y - half_number_of_elements) * self.X)
                if y % 2 == 0:
                    self._drawPixel(border_pos, (0.5 + y - half_number_of_elements) * self.X)

            # Next fill the data section:
            for x in range(dataSize):
                for y in range(dataSize):
                    if self.dataMatrix[y][x] == 1:
                        self._drawPixel((0.5 + x - half_number_of_elements) * self.X, (0.5 + y - half_number_of_elements) * self.X)

            # And finally add a solder mask opening for the whole thing:
            if self.UseCu:
                self._drawSolderMaskOpening((dataSize + 4) * self.X, (dataSize + 4) * self.X, 0)

            #TODO: Add some way to create a keepout zone for nice copper fill behaviour
        else:
            if self.border >= 0:
                # Adding border: Create a new array larger than the self.qr.modules
                sz = self.qr.modules.__len__() + (self.border * 2)
                arrayToDraw = [ [ 0 for a in range(sz) ] for b in range(sz) ]
                lineposition = self.border
                for i in self.qr.modules:
                    columnposition = self.border
                    for j in i:
                        arrayToDraw[lineposition][columnposition] = j
                        columnposition += 1
                    lineposition += 1
            else:
                # No border: using array as is
                arrayToDraw = self.qr.modules

            # used many times...
            half_number_of_elements = arrayToDraw.__len__() / 2

            # Center position of QrCode
            yposition = - int(half_number_of_elements * self.X)
            for line in arrayToDraw:
                xposition = - int(half_number_of_elements * self.X)
                for pixel in line:
                    # Trust table for drawing a pixel
                    # Negative is a boolean;
                    # each pixel is a boolean (need to draw of not)
                    # Negative | Pixel | Result
                    #        0 |     0 | 0
                    #        0 |     1 | 1
                    #        1 |     0 | 1
                    #        1 |     1 | 0
                    # => Draw as Xor
                    if self.negative != pixel: # Xor...
                        self._drawPixel(xposition, yposition)
                    xposition += self.X
                yposition += self.X
            #int((5 + half_number_of_elements) * self.X))
        textPosition = int((self.textHeight) + ((1 + half_number_of_elements) * self.X))
        self.module.Value().SetPosition(pcbnew.wxPoint(0, - textPosition))
        self.module.Reference().SetPosition(pcbnew.wxPoint(0, textPosition))
        self.module.Value().SetLayer(pcbnew.F_SilkS)


DataMatrixWizard().register()
