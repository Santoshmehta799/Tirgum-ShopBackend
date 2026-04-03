import os
import joblib
import numpy as np
from django.conf import settings

# Global variables for lazy loading
_model = None
_encoders = None

def get_model_and_encoders():
    """Lazy load model and encoders when needed"""
    global _model, _encoders
    
    if _model is None or _encoders is None:
        try:
            # Use settings paths directly
            model_path = getattr(settings, 'MODEL_PATH', None)
            encoders_path = getattr(settings, 'ENCODERS_PATH', None)
            
            if model_path and os.path.exists(model_path):
                _model = joblib.load(model_path)
                print(f"Model loaded from: {model_path}")
            else:
                print(f"Warning: Model file not found at {model_path}")
                return None, None
                
            if encoders_path and os.path.exists(encoders_path):
                _encoders = joblib.load(encoders_path)
                print(f"Encoders loaded from: {encoders_path}")
            else:
                print(f"Warning: Encoders file not found at {encoders_path}")
                return None, None
                
        except Exception as e:
            print(f"Error loading model/encoders: {e}")
            return None, None
    
    return _model, _encoders

def predict_net_price(product_instance):
    import logging
    logger = logging.getLogger(__name__)
    
    # Get model and encoders
    model, encoders = get_model_and_encoders()
    
    if model is None or encoders is None:
        logger.error("Model or encoders not available")
        return 0  # Return default value
    
    try:
        brand_encoded = encoders['brand__name'].transform([str(product_instance.brand.name)])[0]
    except (ValueError, KeyError) as e:
        logger.warning(f"Nieznana etykieta brand__name: {product_instance.brand.name}. Ustawiam -1. Error: {e}")
        brand_encoded = -1
    
    try:
        tread_encoded = encoders['tread__name'].transform([str(product_instance.tread.name)])[0]
    except (ValueError, KeyError) as e:
        logger.warning(f"Nieznana etykieta tread__name: {product_instance.tread.name}. Ustawiam -1. Error: {e}")
        tread_encoded = -1
    
    try:
        size_encoded = encoders['size__size'].transform([str(product_instance.size.size)])[0]
    except (ValueError, KeyError) as e:
        logger.warning(f"Nieznana etykieta size__size: {product_instance.size.size}. Ustawiam -1. Error: {e}")
        size_encoded = -1
    
    data = {
        'is_tire_bead_damaged': int(product_instance.is_tire_bead_damaged),
        'is_incised': int(product_instance.is_incised),
        'front_repairs': int(product_instance.front_repairs),
        'is_front_heat_repair': int(product_instance.is_front_heat_repair),
        'is_side_repair': int(product_instance.is_side_repair),
        'is_visible_cracks': int(product_instance.is_visible_cracks),
        'is_braked': int(product_instance.is_braked),
        'is_braked_repair': int(product_instance.is_braked_repair),
        'is_shoulder_repair': int(product_instance.is_shoulder_repair),
        'is_cosmetology': int(product_instance.is_cosmetology),
        'is_toothed_out': int(product_instance.is_toothed_out),
        'is_retreaded': int(product_instance.is_retreaded),
        'is_ruts': int(product_instance.is_ruts),
        'is_circumventional_cut': int(product_instance.is_circumventional_cut),
        'tread_depth_min': int(product_instance.tread_depth_min),
        'tread_depth_max': int(product_instance.tread_depth_max),
        'dot': int(product_instance.dot) if product_instance.dot else 0,
        'brand__name': brand_encoded,
        'tread__name': tread_encoded,
        'size__size': size_encoded,
    }
    
    def round_to_nearest_50(price):
        return int(round(price / 50.0) * 50)
    
    try:
        X = np.array([list(data.values())])
        predicted_price = model.predict(X)[0]
        logger.info(f"Predicted price: {predicted_price}")
        rounded_predicted = round_to_nearest_50(predicted_price)
        return rounded_predicted
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return 0  # Return default value