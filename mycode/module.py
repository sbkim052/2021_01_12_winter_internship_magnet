# References 
# 1. https://people.csail.mit.edu/tiam/deepmag/

import math
import torch

import torch.nn as nn
import numpy as np

# modules
class res_blk(nn.Module):
  def __init__(self, layer_dims, ks, s):
    super(res_blk, self).__init__()
    p = int((ks - 1) / 2)
    self.conv1 = nn.Conv2d(layer_dims, layer_dims, kernel_size=ks, stride=s, padding=p, padding_mode='reflect', bias=False)
    self.activation = nn.ReLU()

  def forward(self, input):
    out = self.conv1(input)
    out = self.activation(out)
    out = self.conv1(out)
    return input + out

def multi_res_blk(num_res_blk, layer_dims, ks, s):
  layers = []
  for i in range(num_res_blk):
    layers.append(res_blk(layer_dims, ks, s))
  return nn.Sequential(*layers)

class res_manipulator(nn.Module):
  def __init__(self, layer_dims=32):
    super(res_manipulator, self).__init__()
    self.conv1 = nn.Conv2d(layer_dims, layer_dims, kernel_size=7, stride=1, padding=3, padding_mode='reflect', bias=False)
    self.conv2 = nn.Conv2d(layer_dims, layer_dims, kernel_size=3, stride=1, padding=1, padding_mode='reflect', bias=False) 
    self.residual = multi_res_blk(1, layer_dims, 3, 1)
    self.activation = nn.ReLU()

  def forward(self, enc_a, enc_b, amp_factor):
    out = enc_b - enc_a
    out = self.activation(self.conv1(out))
    out *= amp_factor
    out = self.conv2(out)
    out = self.residual(out)
    return enc_b + out

class res_encoder(nn.Module):
  def __init__(self, layer_dims=32, num_res_blk=3):
    super(res_encoder, self).__init__()
    self.conv1 = nn.Conv2d(3, int(layer_dims / 2), kernel_size = 7, stride = 1, padding = 3, padding_mode = 'reflect', bias=False)
    self.conv2 = nn.Conv2d(int(layer_dims / 2), layer_dims, kernel_size = 3, stride = 2, padding = 1, padding_mode = 'reflect',bias=False)
    self.residual = multi_res_blk(num_res_blk, layer_dims, 3, 1)
    self.activation = nn.ReLU()

  def forward(self, x):
    out = self.activation(self.conv1(x))
    out = self.activation(self.conv2(out))
    out = self.residual(out)
    return out

class res_decoder(nn.Module):
  def __init__(self, layer_dims=64, num_res_blk=9):
    super(res_decoder, self).__init__()
    self.residual = multi_res_blk(num_res_blk, layer_dims, 3, 1)
    self.up_sample = nn.Upsample(scale_factor = 2, mode = 'nearest')
    self.conv1 = nn.Conv2d(layer_dims, int(layer_dims / 2), kernel_size = 3, stride = 1, padding = 1, padding_mode = 'reflect', bias=False) ## change
    self.conv2 = nn.Conv2d(int(layer_dims / 2), 3, kernel_size = 7, stride = 1, padding = 3, padding_mode = 'reflect', bias=False) ## change
    self.activation = nn.ReLU()

  def forward(self, x):
    out = self.residual(x)
    out = self.up_sample(out)
    out = self.activation(self.conv1(out))
    out = self.conv2(out)
    return out

# magnet
class encoder(nn.Module):
  def __init__(self):
    super(encoder, self).__init__()
    # set variables
    self.num_enc_resblk = 3
    self.res_enc_dim = 32
    self.num_texture_resblk = 2
    self.num_shape_resblk = 2

    # set arch
    self.res_encoder = res_encoder(self.res_enc_dim ,self.num_enc_resblk)
    self.conv_tex = nn.Conv2d(self.res_enc_dim, self.res_enc_dim, kernel_size = 3, stride = 2, padding = 1, padding_mode = 'reflect', bias=False) # stride is 2, cause texture_downsample is True, else 1
    self.conv_sha = nn.Conv2d(self.res_enc_dim, self.res_enc_dim, kernel_size = 3, stride = 1, padding = 1, padding_mode = 'reflect', bias=False)
    self.texture_resblk = multi_res_blk(self.num_texture_resblk, self.res_enc_dim, 3, 1)
    self.shape_resblk = multi_res_blk(self.num_shape_resblk, self.res_enc_dim, 3, 1)
    self.activation = nn.ReLU()

  def forward(self, img):
    enc = self.res_encoder(img)
    texture_enc = enc
    shape_enc = enc
    texture_enc = self.activation(self.conv_tex(texture_enc))
    texture_enc = self.texture_resblk(texture_enc)
    shape_enc = self.activation(self.conv_sha(shape_enc))
    shape_enc = self.shape_resblk(shape_enc)
    return texture_enc, shape_enc

class decoder(nn.Module):
  def __init__(self):
    super(decoder, self).__init__()
    # set variables
    self.num_dec_resblk = 9
    self.texture_dims = 32
    self.shape_dims = 32
    self.decoder_dims = self.texture_dims + self.shape_dims
    
    # set arch
    self.up_sample = nn.Upsample(scale_factor = 2, mode = 'nearest') # texture가 downsampling 됐을 때 activate한다.
    self.conv_tex_aft_upsample = nn.Conv2d(self.texture_dims, self.texture_dims, kernel_size = 3, stride = 1, padding = 1, padding_mode = 'reflect', bias=False)
    self.res_decoder = res_decoder(self.decoder_dims, self.num_dec_resblk)
    self.activation = nn.ReLU()
  
  def forward(self, texture_enc, shape_enc):
    texture_enc = self.up_sample(texture_enc) # texture가 downsampling 됐을 때 activate한다.
    texture_enc = self.activation(self.conv_tex_aft_upsample(texture_enc))
    enc = torch.cat((texture_enc, shape_enc), 1)
    return self.res_decoder(enc)

class magnet(nn.Module):
  def __init__(self):
    super(magnet, self).__init__()
    self.encoder = encoder()
    self.decoder = decoder()
    self.res_manipulator = res_manipulator()

  def forward(self, amplified, image_a, image_b, image_c, amp_factor):
    texture_amp, _ = self.encoder(amplified)
    texture_a, shape_a = self.encoder(image_a)
    texture_b, shape_b = self.encoder(image_b)
    texture_c, shape_c = self.encoder(image_c)
    out_shape_enc = self.res_manipulator(shape_a, shape_b, amp_factor)
    out = self.decoder(texture_b, out_shape_enc)

    return out, texture_a, texture_c, texture_b, texture_amp, shape_b, shape_c