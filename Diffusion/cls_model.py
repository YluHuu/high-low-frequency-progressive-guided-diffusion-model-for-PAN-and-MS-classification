import torch.nn as nn
from torch.nn import functional as F
import torch


class ResBlk(nn.Module):
    """
    resnet block
    """

    def __init__(self, ch_in, ch_out, stride=1):
        """
        :param ch_in:
        :param ch_out:
        """
        super(ResBlk, self).__init__()
        self.conv1 = nn.Conv2d(ch_in, ch_out, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(ch_out)
        self.conv2 = nn.Conv2d(ch_out, ch_out, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(ch_out)

        self.extra = nn.Sequential()
        if ch_out != ch_in:
            # [b, ch_in, h, w] => [b, ch_out, h , w]
            self.extra = nn.Sequential(
                nn.Conv2d(ch_in, ch_out, kernel_size=1, stride=stride),
                nn.BatchNorm2d(ch_out)
            )

    def forward(self, x):
        """
        :param x: [b, ch, h, w]
        :return:
        """
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        # short cut
        # element_wise add:[b, ch_in, h, w] with [b, ch_out, h ,w]
        out = self.extra(x) + out

        return out


class cls_model(nn.Module):

    def __init__(self, output):
        super(cls_model, self).__init__()

        self.output = output
        # ms
        self.conv1 = nn.Sequential(
            nn.Conv2d(4, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64)
        )
        # pan
        self.conv2 = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64)
        )
        # fusion
        self.conv3 = nn.Sequential(
            nn.Conv2d(4, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64)
        )
        # followed 4 blocks
        # [b, 64, h, w] => [b, 128, h , w]
        self.blk1_1 = ResBlk(64, 64, stride=1)
        # [b, 128, h, w] =>[b , 256, h ,w]
        self.blk2_1 = ResBlk(64, 128, stride=1)
        # [b, 256, h, w] =>[b , 512, h ,w]
        self.blk3_1 = ResBlk(128, 256, stride=1)
        # [b, 512, h, w] =>[b , 1024, h ,w]
        self.blk4_1 = ResBlk(256, 512, stride=1)

        self.blk1_2 = ResBlk(64, 64, stride=1)
        # [b, 128, h, w] =>[b , 256, h ,w]
        self.blk2_2 = ResBlk(64, 128, stride=1)
        # [b, 256, h, w] =>[b , 512, h ,w]
        self.blk3_2 = ResBlk(128, 256, stride=1)
        # [b, 512, h, w] =>[b , 1024, h ,w]
        self.blk4_2 = ResBlk(256, 512, stride=1)

        self.blk1_3 = ResBlk(64, 64, stride=1)
        # [b, 128, h, w] =>[b , 256, h ,w]
        self.blk2_3 = ResBlk(64, 128, stride=1)
        # [b, 256, h, w] =>[b , 512, h ,w]
        self.blk3_3 = ResBlk(128, 256, stride=1)
        # [b, 512, h, w] =>[b , 1024, h ,w]
        self.blk4_3 = ResBlk(256, 512, stride=1)

        self.outlayer = nn.Linear(512 * 3, self.output)

    def forward(self, x, y, z):
        """
        x: ms
        y: pan
        z: fusion
        """
        x = F.relu(self.conv1(x))
        # [b, 64, h, w] => [b, 1024, h , w]
        x = self.blk1_1(x)
        x = self.blk2_1(x)
        x = self.blk3_1(x)
        x = self.blk4_1(x)
        x = F.adaptive_avg_pool2d(x, [1, 1])

        y = F.relu(self.conv2(y))
        y = self.blk1_2(y)
        y = self.blk2_2(y)
        y = self.blk3_2(y)
        y = self.blk4_2(y)
        y = F.adaptive_avg_pool2d(y, [1, 1])

        z = F.relu(self.conv3(z))
        z = self.blk1_3(z)
        z = self.blk2_3(z)
        z = self.blk3_3(z)
        z = self.blk4_3(z)
        z = F.adaptive_avg_pool2d(z, [1, 1])

        # print('x', x.shape)
        # print('y', y.shape)
        s = torch.cat([x, y, z], 1)  # 通道拼接
        # print(s.size())
        s = s.view(s.size()[0], -1)
        # print('ssss', s.shape)
        s = self.outlayer(s)
        # print('ssssssssss',s.shape)
        return s