import logging
import os
from typing import Annotated


import vtk
import qt

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLMarkupsFiducialNode, vtkMRMLModelNode


#
# MyFirstModule
#


class MyFirstModule(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Center of Mass")  # TODO: make this more human readable by adding spaces
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Alejandro"]  # TODO: replace with "Firstname Lastname (Organization)"
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#MyFirstModule">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    SampleData.SampleDataLogic.registerCustomSampleDataCategory("MyFirstModule", title=_("MyFirstModule"))

    # MyFirstModule1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="MyFirstModule",
        sampleName="MyFirstModule1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "MyFirstModule1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="MyFirstModule1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="MyFirstModule1",
    )

    # MyFirstModule2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="MyFirstModule",
        sampleName="MyFirstModule2",
        thumbnailFileName=os.path.join(iconsPath, "MyFirstModule2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="MyFirstModule2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="MyFirstModule2",
    )


#
# MyFirstModuleParameterNode
#


@parameterNodeWrapper
class MyFirstModuleParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLMarkupsFiducialNode
    #nodo donde se guarda la esfera
    outputModel: vtkMRMLModelNode

    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# MyFirstModuleWidget
#


class MyFirstModuleWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    #automaticamente se crean dos puntos de ejemplo para probar el módulo, así no hay que crear un nodo de puntos y agregarle puntos manualmente para probarlo
    def onCreateDemoPointsButton(self) -> None:
        """Create two demo markup points in the selected point list."""
        inputPoints = self.ui.inputSelector.currentNode()

        if not inputPoints:
            inputPoints = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLMarkupsFiducialNode",
                "DemoPoints"
            )
            self.ui.inputSelector.setCurrentNode(inputPoints)

        inputPoints.RemoveAllControlPoints()
        inputPoints.AddControlPoint(vtk.vtkVector3d(0, 0, 0), "P1")
        inputPoints.AddControlPoint(vtk.vtkVector3d(30, 0, 0), "P2")

        logging.info(
            f"Created {inputPoints.GetNumberOfControlPoints()} demo points "
            f"in {inputPoints.GetName()}"
        )

        self._checkCanApply()
    
    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/MyFirstModule.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)
        
        self.ui.inputSelector.setProperty("SlicerParameterName", "inputVolume")
        self.ui.inputSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.ui.inputSelector.selectNodeUponCreation = True
        self.ui.inputSelector.addEnabled = True
        self.ui.inputSelector.removeEnabled = True
        self.ui.inputSelector.noneEnabled = False
                
        self.ui.outputSelector.setProperty("SlicerParameterName", "outputModel")
        self.ui.outputSelector.nodeTypes = ["vtkMRMLModelNode"]
        self.ui.outputSelector.selectNodeUponCreation = True
        self.ui.outputSelector.addEnabled = True
        self.ui.outputSelector.removeEnabled = True
        self.ui.outputSelector.renameEnabled = True
        self.ui.outputSelector.noneEnabled = False
        self.ui.outputSelector.baseName = "SphereModel"

        # Result labels added from Python to keep the UI simple.
        self.resultFormLayout = qt.QFormLayout()

        self.centerOfMassValueLabel = qt.QLabel("Not computed yet")
        self.centerOfMassValueLabel.objectName = "centerOfMassValueLabel"
        self.resultFormLayout.addRow("Center of mass:", self.centerOfMassValueLabel)
        
        self.createDemoPointsButton = qt.QPushButton("Create demo points")
        self.createDemoPointsButton.toolTip = "Create two sample markup points for testing"
        self.resultFormLayout.addRow("Demo:", self.createDemoPointsButton)
        
        self.sphereCenterValueLabel = qt.QLabel("Not computed yet")
        self.sphereCenterValueLabel.objectName = "sphereCenterValueLabel"
        self.resultFormLayout.addRow("Sphere center:", self.sphereCenterValueLabel)

        self.sphereRadiusValueLabel = qt.QLabel("Not computed yet")
        self.sphereRadiusValueLabel.objectName = "sphereRadiusValueLabel"
        self.resultFormLayout.addRow("Sphere radius:", self.sphereRadiusValueLabel)

        self.layout.addLayout(self.resultFormLayout)
        
        
        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = MyFirstModuleLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.createDemoPointsButton.connect("clicked(bool)", self.onCreateDemoPointsButton)
        self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self._checkCanApply)
        self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self._checkCanApply)
        

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLMarkupsFiducialNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: MyFirstModuleParameterNode | None) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    #para que el boton apply se active cuando haya al menos 1 punto porque no me salia para activar
    ##update: ahora se necesitan dos puntos y un modelo de salida para activar el botón, así que se puede calcular el centro de masa y crear la esfera
    def _checkCanApply(self, caller=None, event=None) -> None:
        inputPoints = self.ui.inputSelector.currentNode()
        outputModel = self.ui.outputSelector.currentNode()

        if not inputPoints:
            self.ui.applyButton.toolTip = _("Select input points")
            self.ui.applyButton.enabled = False
        elif inputPoints.GetNumberOfControlPoints() < 2:
            self.ui.applyButton.toolTip = _("Add at least two markup points")
            self.ui.applyButton.enabled = False
        elif not outputModel:
            self.ui.applyButton.toolTip = _("Select or create an output model")
            self.ui.applyButton.enabled = False
        else:
            self.ui.applyButton.toolTip = _("Compute center of mass and create sphere")
            self.ui.applyButton.enabled = True

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        # TODO: If your module requires additional Python packages, uncomment
        # the following lines and add your dependencies to the
        # Resources/requirements.txt file (one per line, e.g. "scikit-image>=0.20").
        # import slicer.packaging
        # slicer.packaging.pip_ensure(
        #     slicer.packaging.load_requirements(self.resourcePath("requirements.txt")),
        #     requester="MyFirstModule",
        # )
        
        #hacemos el texto bonito con dos decimales y lo mostramos en la etiqueta
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            centerOfMass = self.logic.getCenterOfMass(self.ui.inputSelector.currentNode())

            centerOfMassText = (
                f"[{centerOfMass[0]:.2f}, "
                f"{centerOfMass[1]:.2f}, "
                f"{centerOfMass[2]:.2f}]"
            )

            self.centerOfMassValueLabel.text = centerOfMassText

            logging.info(f"Computed center of mass: {centerOfMassText}")
            print(f"Computed center of mass: {centerOfMassText}")

#
# MyFirstModuleLogic
#


class MyFirstModuleLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return MyFirstModuleParameterNode(super().getParameterNode())

    
    def getCenterOfMass(self, markupsNode):
        if not markupsNode:
            raise ValueError("Input markups node is invalid")

        numberOfPoints = markupsNode.GetNumberOfControlPoints()
        if numberOfPoints == 0:
            raise ValueError("Input markups node must contain at least one point")

        sumPosition = [0.0, 0.0, 0.0]
        position = [0.0, 0.0, 0.0]

        for pointIndex in range(numberOfPoints):
            markupsNode.GetNthControlPointPosition(pointIndex, position)
            sumPosition[0] += position[0]
            sumPosition[1] += position[1]
            sumPosition[2] += position[2]

        centerOfMass = [
            sumPosition[0] / numberOfPoints,
            sumPosition[1] / numberOfPoints,
            sumPosition[2] / numberOfPoints,
        ]

        logging.info(f"Center of mass for {markupsNode.GetName()}: {centerOfMass}")
        return centerOfMass
    
    
    
    
    
    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

    
    


#
# MyFirstModuleTest
#


class MyFirstModuleTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_MyFirstModule1()

    def test_MyFirstModule1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("MyFirstModule1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = MyFirstModuleLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
