import torch
import torch.nn as nn
import torch.nn.functional as F


class SEBlock(nn.Module):
    def __init__(self, in_channels, reduction=8):
        super(SEBlock, self).__init__()
        reduced = max(1, in_channels // reduction)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, reduced, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(reduced, in_channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        B, C, H, W = x.shape
        y = F.adaptive_avg_pool2d(x, 1).view(B, C)
        y = self.fc(y).view(B, C, 1, 1)
        return x * y


class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1,
                 padding=1, use_se=True):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride,
                              padding, bias=False)
        self.norm = nn.BatchNorm2d(out_channels)
        self.act = nn.LeakyReLU(0.2, inplace=True)
        self.se = SEBlock(out_channels) if use_se else nn.Identity()

    def forward(self, x):
        return self.se(self.act(self.norm(self.conv(x))))


class InvertedResBlock(nn.Module):
    def __init__(self, in_channels, out_channels, expand_ratio=2, use_se=True):
        super(InvertedResBlock, self).__init__()
        hidden_dim = in_channels * expand_ratio
        self.use_res = in_channels == out_channels

        self.conv1 = nn.Conv2d(in_channels, hidden_dim, 1, 1, 0, bias=False)
        self.norm1 = nn.BatchNorm2d(hidden_dim)
        self.act1 = nn.LeakyReLU(0.2, inplace=True)

        self.depthwise = nn.Conv2d(hidden_dim, hidden_dim, 3, 1, 1,
                                   groups=hidden_dim, bias=False)
        self.norm2 = nn.BatchNorm2d(hidden_dim)
        self.act2 = nn.LeakyReLU(0.2, inplace=True)

        self.se = SEBlock(hidden_dim) if use_se else nn.Identity()

        self.conv2 = nn.Conv2d(hidden_dim, out_channels, 1, 1, 0, bias=False)
        self.norm3 = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        out = self.act1(self.norm1(self.conv1(x)))
        out = self.act2(self.norm2(self.depthwise(out)))
        out = self.se(out)
        out = self.norm3(self.conv2(out))
        if self.use_res:
            out = out + x
        return out


class DecoderBlock(nn.Module):
    def __init__(self, in_channels, skip_channels, out_channels):
        super(DecoderBlock, self).__init__()
        self.up = nn.Sequential(
            nn.Conv2d(in_channels, out_channels * 4, 3, 1, 1, bias=False),
            nn.PixelShuffle(2),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.conv1 = ConvBlock(out_channels + skip_channels, out_channels, use_se=False)
        self.conv2 = ConvBlock(out_channels, out_channels, use_se=False)

    def forward(self, x, skip):
        x = self.up(x)
        if x.shape[2:] != skip.shape[2:]:
            x = F.interpolate(x, size=skip.shape[2:], mode="bilinear",
                              align_corners=False)
        x = torch.cat([x, skip], dim=1)
        x = self.conv1(x)
        return self.conv2(x)


class DownBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DownBlock, self).__init__()
        self.conv1 = ConvBlock(in_channels, out_channels, stride=2, use_se=False)
        self.conv2 = InvertedResBlock(out_channels, out_channels)

    def forward(self, x):
        x = self.conv1(x)
        return self.conv2(x)


class ShuffleCUGANModel(nn.Module):
    def __init__(self, model_version="adore", scale=2):
        super(ShuffleCUGANModel, self).__init__()
        self.model_version = model_version
        self.scale = scale

        if model_version == "fallin_soft":
            base_c = 64
            enc_channels = [base_c, base_c * 2, base_c * 4]
        else:
            base_c = 32
            enc_channels = [base_c, base_c * 2, base_c * 4, base_c * 8]

        self.head = ConvBlock(3, enc_channels[0], use_se=False)

        self.encoder = nn.ModuleList()
        for i in range(len(enc_channels) - 1):
            self.encoder.append(DownBlock(enc_channels[i], enc_channels[i + 1]))

        self.bottleneck = nn.Sequential(
            InvertedResBlock(enc_channels[-1], enc_channels[-1]),
            InvertedResBlock(enc_channels[-1], enc_channels[-1]),
        )

        num_decoder = len(enc_channels) - 1
        self.decoder = nn.ModuleList()
        for i in range(num_decoder):
            in_ch = enc_channels[-(i + 1)]
            skip_ch = enc_channels[-(i + 2)]
            out_ch = enc_channels[-(i + 2)]
            self.decoder.append(DecoderBlock(in_ch, skip_ch, out_ch))

        self.upscale_head = nn.Sequential(
            ConvBlock(enc_channels[0], enc_channels[0], use_se=False),
            nn.Conv2d(enc_channels[0], 3 * scale * scale, 3, 1, 1, bias=True),
            nn.PixelShuffle(scale),
        )

    def forward(self, x):
        feats = []
        out = self.head(x)
        feats.append(out)

        for enc in self.encoder:
            out = enc(out)
            feats.append(out)

        out = self.bottleneck(out)

        for i in range(len(self.decoder)):
            skip = feats[-(i + 2)]
            out = self.decoder[i](out, skip)

        out = self.upscale_head(out)
        return torch.clamp(out, 0, 1)
