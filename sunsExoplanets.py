atmospheres = [
    {
        "name": "Mercury",
        "type": "Terrestrial",
        "composition": {"H": "Present", "He": "Present", "O2": "Present", "Na": "Present", "K": "Present"}
    },
    {
        "name": "Venus",
        "type": "Terrestrial",
        "composition": {"CO2": 96.5, "N2": 3.5, "SO2": "Trace"}
    },
    {
        "name": "Earth",
        "type": "Terrestrial",
        "composition": {"N2": 78.08, "O2": 20.95, "Ar": 0.93, "CO2": 0.04}
    },
    {
        "name": "Mars",
        "type": "Terrestrial",
        "composition": {"CO2": 95.3, "N2": 2.7, "Ar": 1.6, "O2": 0.13}
    },
    {
        "name": "Jupiter",
        "type": "Gas Giant",
        "composition": {"H2": 89.8, "He": 10.2, "CH4": 0.3}
    },
    {
        "name": "Saturn",
        "type": "Gas Giant",
        "composition": {"H2": 96.3, "He": 3.2, "CH4": 0.4}
    },
    {
        "name": "Uranus",
        "type": "Ice Giant",
        "composition": {"H2": 82.5, "He": 15.2, "CH4": 2.3}
    },
    {
        "name": "Neptune",
        "type": "Ice Giant",
        "composition": {"H2": 80.0, "He": 19.0, "CH4": 1.5}
    },
    {
        "name": "WASP-39b",
        "type": "Exoplanet (Hot Saturn)",
        "composition": {"CO2": "Present", "H2O": "Present", "SO2": "Present", "CO": "Present"}
    },
    {
        "name": "K2-18b",
        "type": "Exoplanet (Hycean candidate)",
        "composition": {"H2": "Major", "CH4": "Present", "CO2": "Present"}
    },
    {
        "name": "HD 209458b",
        "type": "Exoplanet (Hot Jupiter)",
        "composition": {"H": "Present", "He": "Present", "H2O": "Present", "CO": "Present"}
    },
    {
        "name": "HD 189733b",
        "type": "Exoplanet (Hot Jupiter)",
        "composition": {"H2O": "Present", "CH4": "Present", "NH3": "Trace"}
    },
    {
        "name": "55 Cancri e",
        "type": "Exoplanet (Super-Earth)",
        "composition": {"CO": "Likely", "N2": "Likely"}
    }
]

# Values for absorption depth (ppm) are representative of typical 
# observations (e.g., JWST for exoplanets) and vary by planet size.
planetary_spectroscopy = [
    {
        "planet": "Earth",
        "observations": {
            "O3": {
                "peak_wavelength_microns": 9.6,
                "absorption_depth": "Significant",
                "spectral_fingerprint": "Chappuis and Hartley bands",
                "transition_type": "Electronic/Vibrational"
            },
            "H2O": {
                "peak_wavelength_microns": 1.4,
                "absorption_depth": "Variable",
                "spectral_fingerprint": "Vibrational-rotational bands",
                "transition_type": "Vibrational"
            }
        }
    },
    {
        "planet": "WASP-39b",
        "observations": {
            "CO2": {
                "peak_wavelength_microns": 4.3,
                "absorption_depth_ppm": 1100,
                "spectral_fingerprint": "Strong 4.3 micron doublet",
                "transition_type": "Asymmetric Stretch"
            },
            "SO2": {
                "peak_wavelength_microns": 4.05,
                "absorption_depth_ppm": 300,
                "spectral_fingerprint": "Photochemical byproduct signature",
                "transition_type": "Vibrational"
            }
        }
    },
    {
        "planet": "K2-18b",
        "observations": {
            "CH4": {
                "peak_wavelength_microns": 3.3,
                "absorption_depth_ppm": 500,
                "spectral_fingerprint": "C-H stretching fundamental",
                "transition_type": "Vibrational"
            },
            "CO2": {
                "peak_wavelength_microns": 4.3,
                "absorption_depth_ppm": 400,
                "spectral_fingerprint": "Bending mode transition",
                "transition_type": "Vibrational"
            }
        }
    },
    {
        "planet": "Jupiter",
        "observations": {
            "NH3": {
                "peak_wavelength_microns": 10.5,
                "absorption_depth": "High",
                "spectral_fingerprint": "Inversion transition",
                "transition_type": "Molecular Inversion"
            },
            "CH4": {
                "peak_wavelength_microns": 7.7,
                "absorption_depth": "High",
                "spectral_fingerprint": "Pentad band system",
                "transition_type": "Vibrational"
            }
        }
    }
]
