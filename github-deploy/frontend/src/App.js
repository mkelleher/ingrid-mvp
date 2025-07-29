import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { FiCamera, FiHeart, FiClock, FiSearch, FiUpload } from 'react-icons/fi';
import { MdOutlineClose, MdOutlineCameraAlt } from 'react-icons/md';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Generate session ID for anonymous tracking
const getSessionId = () => {
  let sessionId = localStorage.getItem('ingrid_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('ingrid_session_id', sessionId);
  }
  return sessionId;
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ScanScreen />} />
          <Route path="/result" element={<ResultScreen />} />
          <Route path="/history" element={<HistoryScreen />} />
          <Route path="/favorites" element={<FavoritesScreen />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

// Navigation Component
const Navigation = ({ activeTab }) => {
  const navigate = useNavigate();
  
  const handleTabClick = (path) => {
    navigate(path);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2">
      <div className="flex justify-around items-center">
        <button
          onClick={() => handleTabClick('/')}
          className={`flex flex-col items-center p-2 ${
            activeTab === 'scan' ? 'text-green-600' : 'text-gray-500'
          }`}
        >
          <FiSearch size={24} />
          <span className="text-xs mt-1">Scan</span>
        </button>
        
        <button
          onClick={() => handleTabClick('/history')}
          className={`flex flex-col items-center p-2 ${
            activeTab === 'history' ? 'text-green-600' : 'text-gray-500'
          }`}
        >
          <FiClock size={24} />
          <span className="text-xs mt-1">History</span>
        </button>
        
        <button
          onClick={() => handleTabClick('/favorites')}
          className={`flex flex-col items-center p-2 ${
            activeTab === 'favorites' ? 'text-green-600' : 'text-gray-500'
          }`}
        >
          <FiHeart size={24} />
          <span className="text-xs mt-1">Favorites</span>
        </button>
      </div>
    </div>
  );
};

// Scan Screen Component
const ScanScreen = () => {
  const [activeTab] = useState('scan');
  const [scanMode, setScanMode] = useState('barcode'); // Start with barcode for simplicity
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleBarcodeResult = async (barcode) => {
    setLoading(true);
    try {
      const sessionId = getSessionId();
      const response = await axios.post(`${API}/scan/barcode`, {
        barcode: barcode,
        session_id: sessionId
      });
      
      // Store result for display
      localStorage.setItem('scan_result', JSON.stringify(response.data));
      navigate('/result');
    } catch (error) {
      console.error('Error scanning barcode:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to scan barcode. Please try again.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoScan = async (imageFile) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('session_id', getSessionId());
      
      const response = await axios.post(`${API}/scan/ocr`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      localStorage.setItem('scan_result', JSON.stringify(response.data));
      navigate('/result');
    } catch (error) {
      console.error('Error scanning photo:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to scan photo. Please try again.';
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white px-4 py-6 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800 text-center">Ingrid</h1>
        <p className="text-gray-600 text-center mt-1">Clean eating made simple</p>
      </div>

      {/* Scan Mode Selection */}
      <div className="p-4">
        <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
          <button
            onClick={() => setScanMode('barcode')}
            className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-colors ${
              scanMode === 'barcode'
                ? 'bg-white text-green-600 shadow-sm'
                : 'text-gray-600'
            }`}
          >
            <FiSearch className="inline mr-2" />
            Barcode
          </button>
          <button
            onClick={() => setScanMode('photo')}
            className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-colors ${
              scanMode === 'photo'
                ? 'bg-white text-green-600 shadow-sm'
                : 'text-gray-600'
            }`}
          >
            <FiUpload className="inline mr-2" />
            Photo
          </button>
        </div>

        {/* Scan Interface */}
        {scanMode === 'barcode' && (
          <BarcodeScanner onResult={handleBarcodeResult} loading={loading} />
        )}
        
        {scanMode === 'photo' && (
          <PhotoUploader onResult={handlePhotoScan} loading={loading} />
        )}
      </div>

      <Navigation activeTab={activeTab} />
    </div>
  );
};

// Barcode Scanner Component
const BarcodeScanner = ({ onResult, loading }) => {
  const [scanner, setScanner] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [manualBarcode, setManualBarcode] = useState('');
  const [showManualEntry, setShowManualEntry] = useState(false);

  useEffect(() => {
    if (isScanning) {
      const qrScanner = new Html5QrcodeScanner(
        "barcode-reader",
        { 
          fps: 10, 
          qrbox: { width: 250, height: 250 },
          aspectRatio: 1.0,
          showTorchButtonIfSupported: true,
        },
        false
      );

      qrScanner.render(
        (decodedText) => {
          qrScanner.clear();
          setIsScanning(false);
          onResult(decodedText);
        },
        (error) => {
          // Handle scan errors silently
        }
      );

      setScanner(qrScanner);

      return () => {
        if (qrScanner) {
          qrScanner.clear();
        }
      };
    }
  }, [isScanning, onResult]);

  const startScanning = () => {
    setIsScanning(true);
    setShowManualEntry(false);
  };

  const stopScanning = () => {
    if (scanner) {
      scanner.clear();
    }
    setIsScanning(false);
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (manualBarcode.trim()) {
      onResult(manualBarcode.trim());
      setManualBarcode('');
    }
  };

  const toggleManualEntry = () => {
    setShowManualEntry(!showManualEntry);
    if (isScanning) {
      stopScanning();
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Looking up product...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg overflow-hidden shadow-sm">
      {!isScanning && !showManualEntry ? (
        <div className="p-8 text-center">
          <FiSearch size={64} className="mx-auto mb-4 text-green-600" />
          <h3 className="text-lg font-semibold mb-2">Scan Product Barcode</h3>
          <p className="text-gray-600 mb-6">
            Point your camera at the product barcode to get ingredient analysis
          </p>
          <div className="space-y-3">
            <button
              onClick={startScanning}
              className="w-full bg-green-600 text-white px-8 py-3 rounded-full shadow-lg hover:bg-green-700 transition-colors"
            >
              📷 Start Camera Scanning
            </button>
            <button
              onClick={toggleManualEntry}
              className="w-full bg-blue-600 text-white px-8 py-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
            >
              ⌨️ Enter Barcode Manually
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Having trouble with camera? Use manual entry instead
          </p>
        </div>
      ) : showManualEntry ? (
        <div className="p-8">
          <h3 className="text-lg font-semibold mb-4 text-center">Enter Barcode Manually</h3>
          <form onSubmit={handleManualSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Product Barcode (UPC/EAN)
              </label>
              <input
                type="text"
                value={manualBarcode}
                onChange={(e) => setManualBarcode(e.target.value)}
                placeholder="e.g. 3017620422003"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                pattern="[0-9]{8,14}"
                title="Enter 8-14 digit barcode"
              />
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={!manualBarcode.trim()}
                className="flex-1 bg-green-600 text-white px-6 py-3 rounded-full hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                🔍 Look Up Product
              </button>
              <button
                type="button"
                onClick={toggleManualEntry}
                className="flex-1 bg-gray-600 text-white px-6 py-3 rounded-full hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
          <p className="text-xs text-gray-500 mt-4 text-center">
            Find the barcode on your product packaging (usually 8-14 digits)
          </p>
        </div>
      ) : (
        <div>
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-yellow-400">⚠️</span>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Camera Permission Required:</strong> Please allow camera access when prompted, then point your camera at the barcode.
                </p>
                <p className="text-xs text-yellow-600 mt-1">
                  Having trouble? Try the "Enter Manually" option below.
                </p>
              </div>
            </div>
          </div>
          <div id="barcode-reader" className="w-full"></div>
          <div className="p-4 text-center space-y-2">
            <button
              onClick={stopScanning}
              className="bg-gray-600 text-white px-6 py-2 rounded-full hover:bg-gray-700 transition-colors mr-3"
            >
              Stop Scanning
            </button>
            <button
              onClick={toggleManualEntry}
              className="bg-blue-600 text-white px-6 py-2 rounded-full hover:bg-blue-700 transition-colors"
            >
              Enter Manually Instead
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Photo Uploader Component
const PhotoUploader = ({ onResult, loading }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = () => {
    if (selectedImage) {
      onResult(selectedImage);
    }
  };

  const handleClear = () => {
    setSelectedImage(null);
    setPreview(null);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Analyzing ingredients...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg overflow-hidden shadow-sm">
      {!preview ? (
        <div className="p-8 text-center">
          <FiUpload size={64} className="mx-auto mb-4 text-green-600" />
          <h3 className="text-lg font-semibold mb-2">Upload Product Photo</h3>
          <p className="text-gray-600 mb-4">
            Choose a clear photo of the product's ingredient label
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800 font-medium mb-2">📸 Photo Tips:</p>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Make sure ingredient list is clearly visible</li>
              <li>• Use good lighting (avoid shadows)</li>
              <li>• Keep text straight and in focus</li>
              <li>• Include the full ingredient section</li>
            </ul>
          </div>
          <label className="bg-green-600 text-white px-8 py-3 rounded-full shadow-lg hover:bg-green-700 transition-colors cursor-pointer inline-block">
            📷 Choose Photo
            <input
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />
          </label>
          <p className="text-xs text-gray-500 mt-4">
            Supports JPG, PNG, and other image formats
          </p>
        </div>
      ) : (
        <div>
          <div className="relative">
            <img src={preview} alt="Selected" className="w-full aspect-square object-cover" />
            <button
              onClick={handleClear}
              className="absolute top-4 right-4 bg-white bg-opacity-80 p-2 rounded-full hover:bg-opacity-100 transition-all"
            >
              <MdOutlineClose size={20} />
            </button>
          </div>
          <div className="p-4 text-center">
            <button
              onClick={handleAnalyze}
              className="bg-green-600 text-white px-8 py-3 rounded-full shadow-lg hover:bg-green-700 transition-colors mr-4"
            >
              Analyze Photo
            </button>
            <button
              onClick={handleClear}
              className="bg-gray-600 text-white px-6 py-3 rounded-full hover:bg-gray-700 transition-colors"
            >
              Choose Different
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Result Screen Component
const ResultScreen = () => {
  const [result, setResult] = useState(null);
  const [activeTab] = useState('scan');
  const navigate = useNavigate();

  useEffect(() => {
    const storedResult = localStorage.getItem('scan_result');
    if (storedResult) {
      setResult(JSON.parse(storedResult));
    } else {
      navigate('/');
    }
  }, [navigate]);

  const toggleBookmark = async () => {
    if (!result) return;

    try {
      const sessionId = getSessionId();
      const response = await axios.post(`${API}/bookmarks/toggle`, null, {
        params: {
          session_id: sessionId,
          product_id: result.product.id
        }
      });

      setResult(prev => ({
        ...prev,
        is_bookmarked: response.data.bookmarked
      }));
    } catch (error) {
      console.error('Error toggling bookmark:', error);
    }
  };

  const getRatingColor = (rating) => {
    switch (rating) {
      case 'green': return 'bg-green-500';
      case 'amber': return 'bg-yellow-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getRatingText = (rating) => {
    switch (rating) {
      case 'green': return 'Clean Choice';
      case 'amber': return 'Moderate';
      case 'red': return 'Complex';
      default: return 'Unknown';
    }
  };

  if (!result) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white px-4 py-6 shadow-sm flex items-center">
        <button
          onClick={() => navigate('/')}
          className="mr-4 p-2 hover:bg-gray-100 rounded-full"
        >
          <MdOutlineClose size={24} />
        </button>
        <h1 className="text-xl font-semibold">Scan Result</h1>
        <button
          onClick={toggleBookmark}
          className="ml-auto p-2 hover:bg-gray-100 rounded-full"
        >
          <FiHeart
            size={24}
            className={result.is_bookmarked ? 'text-red-500 fill-current' : 'text-gray-400'}
          />
        </button>
      </div>

      <div className="p-4 space-y-6">
        {/* Product Info */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-2">{result.product.name}</h2>
          {result.product.brand && (
            <p className="text-gray-600 mb-4">{result.product.brand}</p>
          )}
          
          {/* Rating */}
          <div className="flex items-center mb-4">
            <div className={`w-8 h-8 rounded-full ${getRatingColor(result.product.rating)} mr-3`}></div>
            <div>
              <p className="font-semibold">{getRatingText(result.product.rating)}</p>
              <p className="text-sm text-gray-600">{result.product.ingredient_count} ingredients</p>
            </div>
          </div>

          {/* Certifications */}
          {result.product.certifications.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Certifications:</p>
              <div className="flex flex-wrap gap-2">
                {result.product.certifications.map((cert, index) => (
                  <span
                    key={index}
                    className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                  >
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Ingredients */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Ingredients ({result.product.ingredient_count})</h3>
          {result.product.ingredients.length > 0 ? (
            <div className="space-y-2">
              {result.product.ingredients.map((ingredient, index) => (
                <div key={index} className="flex items-center py-2 border-b border-gray-100 last:border-b-0">
                  <span className="text-sm text-gray-600 mr-3">{index + 1}.</span>
                  <span className="flex-1">{ingredient}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No ingredients detected</p>
          )}
        </div>

        {/* Rating Guide */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Rating Guide</h3>
          <div className="space-y-3">
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-full bg-green-500 mr-3"></div>
              <span className="text-sm"><strong>Clean Choice:</strong> 4 or fewer ingredients</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-full bg-yellow-500 mr-3"></div>
              <span className="text-sm"><strong>Moderate:</strong> 5-9 ingredients</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-full bg-red-500 mr-3"></div>
              <span className="text-sm"><strong>Complex:</strong> 10+ ingredients</span>
            </div>
          </div>
        </div>
      </div>

      <Navigation activeTab={activeTab} />
    </div>
  );
};

// History Screen Component
const HistoryScreen = () => {
  const [activeTab] = useState('history');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const sessionId = getSessionId();
      const response = await axios.get(`${API}/history/${sessionId}`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewResult = (result) => {
    localStorage.setItem('scan_result', JSON.stringify(result));
    window.location.href = '/result';
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white px-4 py-6 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800 text-center">Scan History</h1>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-12">
            <FiClock size={64} className="mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No scans yet</h3>
            <p className="text-gray-500">Your scan history will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((item, index) => (
              <ProductCard
                key={index}
                product={item.product}
                isBookmarked={item.is_bookmarked}
                onClick={() => viewResult(item)}
              />
            ))}
          </div>
        )}
      </div>

      <Navigation activeTab={activeTab} />
    </div>
  );
};

// Favorites Screen Component
const FavoritesScreen = () => {
  const [activeTab] = useState('favorites');
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const sessionId = getSessionId();
      const response = await axios.get(`${API}/bookmarks/${sessionId}`);
      setFavorites(response.data);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewResult = (result) => {
    localStorage.setItem('scan_result', JSON.stringify(result));
    window.location.href = '/result';
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white px-4 py-6 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800 text-center">Favorites</h1>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading favorites...</p>
          </div>
        ) : favorites.length === 0 ? (
          <div className="text-center py-12">
            <FiHeart size={64} className="mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No favorites yet</h3>
            <p className="text-gray-500">Tap the heart icon to bookmark products</p>
          </div>
        ) : (
          <div className="space-y-4">
            {favorites.map((item, index) => (
              <ProductCard
                key={index}
                product={item.product}
                isBookmarked={true}
                onClick={() => viewResult(item)}
              />
            ))}
          </div>
        )}
      </div>

      <Navigation activeTab={activeTab} />
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product, isBookmarked, onClick }) => {
  const getRatingColor = (rating) => {
    switch (rating) {
      case 'green': return 'bg-green-500';
      case 'amber': return 'bg-yellow-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getRatingText = (rating) => {
    switch (rating) {
      case 'green': return 'Clean';
      case 'amber': return 'Moderate';
      case 'red': return 'Complex';
      default: return 'Unknown';
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-lg mb-1">{product.name}</h3>
          {product.brand && (
            <p className="text-gray-600 text-sm mb-2">{product.brand}</p>
          )}
          
          <div className="flex items-center mb-2">
            <div className={`w-4 h-4 rounded-full ${getRatingColor(product.rating)} mr-2`}></div>
            <span className="text-sm text-gray-600">
              {getRatingText(product.rating)} • {product.ingredient_count} ingredients
            </span>
          </div>

          {product.certifications.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {product.certifications.map((cert, index) => (
                <span
                  key={index}
                  className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs"
                >
                  {cert}
                </span>
              ))}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {isBookmarked && (
            <FiHeart className="text-red-500 fill-current" size={20} />
          )}
        </div>
      </div>
    </div>
  );
};

export default App;