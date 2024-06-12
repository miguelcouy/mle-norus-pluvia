# -*- coding: utf-8 -*-
from typing import Literal

settings = {
    "global_config": {
        "sep": ";",
        "decimal": ".",
        "encoding": "utf8",
        "date_format": "%Y-%m-%d",
        "round_float": 3 
    },

    "maps":{
    
    }
}

FILES = Literal[
    "VNA", "Prevs", "Dadvaz", "PMedia", "ENA", "ENAPREVS", "STR"
]

PRECIPITATION_SOURCES = Literal[
    "MERGE", "ETA", "GEFS", "CFS", "Usuário", "Prec. Zero", 
    "ECMWF_ENS", "ECMWF_ENS_EXT", "ONS", "ONS_Pluvia", 
    "ONS_ETAd_1_Pluvia", "GEFS_EXT"
]

FORECAST_MODELS = Literal["IA", "IA+SMAP", "SMAP"]

MODES = Literal["Diário", "Mensal"]