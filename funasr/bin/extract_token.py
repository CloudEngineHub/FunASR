import os
import hydra
import logging
from omegaconf import DictConfig, OmegaConf, ListConfig
import torch
import torch.distributed
from funasr.auto.auto_model import AutoModel



@hydra.main(config_name=None, version_base=None)
def main_hydra(cfg: DictConfig):
    def to_plain_list(cfg_item):
        if isinstance(cfg_item, ListConfig):
            return OmegaConf.to_container(cfg_item, resolve=True)
        elif isinstance(cfg_item, DictConfig):
            return {k: to_plain_list(v) for k, v in cfg_item.items()}
        else:
            return cfg_item

    kwargs = to_plain_list(cfg)

    machine_rank = int(kwargs.get("dist_rank", 0))
    world_size = int(kwargs.get("world_size", 1))
    local_rank = int(os.environ["LOCAL_RANK"])
    node_world_size = int(os.environ["WORLD_SIZE"])
    dist_rank = machine_rank * node_world_size + local_rank
    logging.basicConfig(
        level='INFO',
        format=f"[{os.uname()[1].split('.')[0]}]-[{dist_rank}/{world_size}] "
               f" %(asctime)s (%(module)s:%(lineno)d) %(levelname)s: %(message)s",
    )
    kwargs["input"] = kwargs["input"] + f"{dist_rank:02d}"
    if not kwargs["input"].endswith(".scp"):
        kwargs["input"] += ".scp"
    kwargs["output_dir"] = os.path.join(kwargs["output_dir"], f"{dist_rank:02d}")
    kwargs["device"] = "cuda"
    kwargs["disable_pbar"] = True
    logging.info("start to extract {}.".format(kwargs["input"]))
    logging.info("save to {}.".format(kwargs["output_dir"]))
    logging.info("using device cuda:{}.".format(local_rank))
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))
    model = AutoModel(**kwargs)
    res = model.generate(input=kwargs["input"])
    print(res)


if __name__ == "__main__":
    main_hydra()