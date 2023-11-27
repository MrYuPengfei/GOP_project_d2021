# d20210827
from torch.functional import Tensor
from util.ImageCompressor import Image
from util import *

class Net(nn.Module):
    # 20210913
    # Net(input_image, ref_image)-> recon_frame, mse_loss, align_loss, bpp_offsets, total_bpp
    
    def __init__(self):
        super(Net, self).__init__()
        self.generator = Offset_Generator()
        self.compensation = Compensation()
        self.frame_recon = Frame_recon()
        self.mv_encoder = Analysis_mv_net()
        self.mv_decoder = Synthesis_mv_net()
        self.compressor_mv = FeatureCompressor(out_channel_N=96, out_channel_M=128)
        self.compressor_res = FeatureCompressor(out_channel_N=48, out_channel_M=64)
        self.Q = Quantization()
        self.proEstimator_z = ProEstimator(channel=96)
        self.res_encoder = Analysis_net()
        self.res_decoder = Synthesis_net()
        

    def forward(self, input_image:torch.Tensor, ref_image:torch.Tensor):
        offsets, input_fea, ref_fea = self.generator(ref_image, input_image) #[8, 64, 256, 256]
        feature_mv = self.mv_encoder(offsets) # [8, 128, 16, 16]
        recon_mv, mse_loss_mv,  bits_mv = self.compressor_mv(feature_mv)
        recon_offsets = self.mv_decoder(recon_mv)
        aligned_fea = self.compensation(recon_offsets, ref_fea)
        fea_residual = input_fea - aligned_fea
        recon_res, mse_loss_res,  bits_res = self.compressor_res(fea_residual) 
        recon_fea = aligned_fea + recon_res
        recon_image = self.frame_recon(recon_fea)
        mse_loss_image = torch.mean((input_image - recon_image).pow(2))
        total_bits = bits_mv + bits_res
        bpp = total_bits / (input_image.size()[0] * input_image.size()[2] * input_image.size()[3])
        return  recon_image, input_image, mse_loss_image, mse_loss_res, mse_loss_mv, total_bits, bits_res, bits_mv, bpp


if __name__ == "__main__":
    """Debug"""
    net = Net().cuda()
    x1 = torch.rand(8, 3, 256, 256).cuda()
    x2 = torch.rand(8, 3, 256, 256).cuda() 
    print('recon_frame, mse_loss_image, mse_loss_res, mse_loss_mv, total_bits, bits_res, bits_mv, bpp')
    print(net(x1,x2))
    # for i in [ recon_frame, mse_loss, align_loss, total_bits, mse_loss_mv, mse_loss_res, bpp]:    
    #    print(i)
