import torch
import torch.nn as nn
import torch.nn.functional as F
import torchinfo
import onnx
import torch.onnx

from converter import parse_onnx_model

class SimpleNet(nn.Module):
    def __init__(self, num_classes=10, init_weights=True):
        super(SimpleNet, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=3, kernel_size=4, stride=2)
        self.conv2 = nn.Conv2d(in_channels=3, out_channels=5, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(in_channels=5, out_channels=5, kernel_size=4, stride=2)

        self.linear1 = nn.Linear(in_features=5 * 2 * 2, out_features=10)
        self.linear2 = nn.Linear(in_features=10, out_features=num_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = self.conv3(x)
        x = F.relu(x)
        x = torch.flatten(x, start_dim=1)
        x = self.linear1(x)
        x = F.relu(x)
        x = self.linear2(x)
        return x

def onnx_check_model(onnx_model):
    try:
        onnx.checker.check_model(onnx_model)
    except onnx.checker.ValidationError as e:
        print('The model is invalid: %s' % e)
    else:
        print('The model is valid!')


if __name__ == "__main__":
    model = SimpleNet()

    x = torch.randn(16, 1, 32, 32, requires_grad=True)
    model = model.cpu()
    x = x.cpu()

    # Export the model
    torch.onnx.export(model,                     # model being run
                    x,                         # model input (or a tuple for multiple inputs)
                    "model.onnx",              # where to save the model (can be a file or file-like object)
                    export_params=True,        # store the trained parameter weights inside the model file
                    opset_version=13,          # the ONNX version to export the model to
                    do_constant_folding=True,  # whether to execute constant folding for optimization
                    input_names = ['input'],   # the model's input names
                    output_names = ['output'], # the model's output names
                    dynamic_axes={'input' : {0 : 'batch_size'},    # variable length axes
                                    'output' : {0 : 'batch_size'}})

    model_onnx = onnx.load("model.onnx")
    onnx_check_model(model_onnx)

    ir = parse_onnx_model(model_onnx)
    print(ir)