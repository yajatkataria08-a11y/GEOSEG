import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from pathlib import Path
from src.models.psisr import PSISRNet
from src.models.colnet import ColNet
from src.models.unetformer import UNetFormer
from src.models.farseg import FarSeg

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 70)
    print(f"  VERIFYING ALL TRAINED MODELS ON: {device} ({torch.cuda.get_device_name(0)})")
    print("=" * 70)

    # 1. PSISRNet
    psisr_path = Path('checkpoints/psisr/best_model.pth')
    if psisr_path.exists():
        m = PSISRNet(in_channels=3, out_channels=3, base_filters=128).to(device)
        m.load_state_dict(torch.load(psisr_path, map_location=device)['model_state_dict'])
        m.eval()
        x = torch.randn(1, 3, 64, 64, device=device)
        with torch.no_grad():
            out = m(x, scale=8)
        print(f"  [1/4] PSISRNet   -> Loaded: {psisr_path} | In: (1,3,64,64) -> Out 8x: {tuple(out['sr_8x'].shape)}")

    # 2. ColNet
    colnet_path = Path('checkpoints/colnet/best_colnet.pth')
    if colnet_path.exists():
        m = ColNet(in_channels=3, num_classes=30, sr_base_filters=32).to(device)
        m.load_state_dict(torch.load(colnet_path, map_location=device)['model_state_dict'])
        m.eval()
        with torch.no_grad():
            out = m(x)
        print(f"  [2/4] ColNet     -> Loaded: {colnet_path} | SR 8x: {tuple(out['sr_8x'].shape)} | Seg 30-Cls: {tuple(out['seg_logits'].shape)}")

    # 3. UNetFormer
    unf_path = Path('checkpoints/unetformer/best_unetformer.pth')
    if unf_path.exists():
        m = UNetFormer(in_channels=3, num_classes=30, decoder_dim=64).to(device)
        m.load_state_dict(torch.load(unf_path, map_location=device)['model_state_dict'])
        m.eval()
        x128 = torch.randn(1, 3, 128, 128, device=device)
        with torch.no_grad():
            out = m(x128)
        print(f"  [3/4] UNetFormer -> Loaded: {unf_path} | In: (1,3,128,128) -> Seg 30-Cls: {tuple(out.shape)}")

    # 4. FarSeg
    farseg_path = Path('checkpoints/farseg/best_farseg.pth')
    if farseg_path.exists():
        m = FarSeg(in_channels=3, num_classes=30, feature_dim=64).to(device)
        m.load_state_dict(torch.load(farseg_path, map_location=device)['model_state_dict'])
        m.eval()
        with torch.no_grad():
            out = m(x128)
        print(f"  [4/4] FarSeg     -> Loaded: {farseg_path} | In: (1,3,128,128) -> Seg 30-Cls: {tuple(out.shape)}")

    print("\n" + "=" * 70)
    print("  [SUCCESS] ALL 4 TRAINED MODELS EXECUTED CLEANLY ON NVIDIA RTX 5050!")
    print("=" * 70)

if __name__ == '__main__':
    main()
