// API base URL configuration from environment with fallback to localhost:8000
export const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  'http://localhost:8000'

// The 247 food and ingredient classes supported by the DishGenie CNN model
export const INGREDIENT_CLASSES = [
  'agaricus_bisporus',
  'agaricus_blazei_murill',
  'agrocybe_aegerita',
  'allium',
  'almond',
  'annona_muricata',
  'apple',
  'apricot',
  'arrowhead',
  'artocarpus_heterophyllus',
  'asparagus',
  'asparagus_fern',
  'asparagus_lettuce',
  'asparagus_pea',
  'avocado',
  'azuki_beans',
  'bamboo_shoot',
  'banana',
  'basella_rubra',
  'basil',
  'bayberry',
  'bean',
  'beefsteak_plant',
  'beetroot',
  'bergamot_pear',
  'bird_pepper',
  'bitter_gourd',
  'black_bean_sprouts',
  'black_currant',
  'black_salsify',
  'blood_orange',
  'blueberry',
  'bolete',
  'bottle_gourd',
  'breadfruit',
  'brinjal',
  'broad_bean',
  'broccoli',
  'brussels_sprouts',
  'bunching_onion',
  'burdock_root',
  'cabbage',
  'candied_date',
  'cape_gooseberry',
  'capsicum',
  'carambola',
  'carrot',
  'cashew_nut',
  'cattail',
  'cauliflower',
  'celeriac',
  'celery',
  'chantarelle',
  'cherry',
  'chicory',
  'chinese_artichoke',
  'chinese_cabbage',
  'chinese_chestnut',
  'chinese_kale',
  'chinese_mallow',
  'chinese_pumpkin',
  'chinese_yam',
  'chive',
  'chocho',
  'chrysanthemum',
  'citrus',
  'coconut',
  'coprinus_comatus',
  'coriander',
  'corn',
  'cowpea',
  'cress',
  'crown_pear',
  'cucumber',
  'curly_kale',
  'dandelion',
  'dangshan_pear',
  'day_lily',
  'dekopon',
  'dictyophora',
  'diospyros_lotus',
  'durian',
  'edible_amaranth',
  'endive',
  'enoki_mushroom',
  'feather_cockscomb',
  'fennel',
  'fig',
  'flat_peach',
  'flower_chinese_cabbage',
  'gandaria',
  'garlic',
  'garlic_chive',
  'garlic_sprouts',
  'ginger',
  'ginseng_fruit',
  'globe_artichoke',
  'goji_berry',
  'golden_melon',
  'gorgon_fruit_seed',
  'gourd',
  'grape',
  'grapefruit',
  'green_chinese_onion',
  'green_dates',
  'guava',
  'gynura_bicolor',
  'hairy_squash',
  'hami_melon',
  'hawthorn',
  'hazelnut',
  'hen-of-the-woods',
  'hericium',
  'hickory',
  'honey_dew_melon',
  'housi_pear',
  'houttuynia_cordata',
  'hyacinth_bean',
  'hypsizigus_marmoreus',
  'jerusalem_artichoke',
  'jew\'s-ear',
  'juicy_peach',
  'jujube',
  'kidney_bean',
  'kidney_bean_seed',
  'kiwi_fruit',
  'kohlrabi',
  'konnyaku',
  'kudzu',
  'kumquat',
  'leaf_lettuce',
  'leek',
  'lemon',
  'lettuce',
  'lily',
  'lime',
  'litchi',
  'longan',
  'loquat',
  'lotus',
  'lotus_root',
  'lotus_seed',
  'lotus_seedpod',
  'luffa_acutangula',
  'luffa_cylindrica',
  'macadamia',
  'mandarin_orange',
  'mango',
  'mangosteen',
  'matsutake',
  'mint',
  'mioga_ginger',
  'mitsuba',
  'morel',
  'mung_bean',
  'mung_bean_sprouts',
  'munlberry',
  'muskmelon',
  'mustard',
  'nameko',
  'naseberry',
  'navel_orange',
  'nectarine',
  'netted_melon',
  'new_zealand_spinach',
  'okra',
  'olive',
  'onion',
  'orange',
  'oyster_mushroom',
  'pakchoi',
  'papaya',
  'parsley',
  'parsnip',
  'passion_fruit',
  'pea',
  'peanut_sprouts',
  'pecans',
  'pepper',
  'persimmon',
  'pineapple',
  'pistachio',
  'pitaya',
  'platycodon_grandiflorum',
  'pleurotus_eryngii',
  'pleurotus_nebrodensis',
  'plum',
  'plum-leaf_crab',
  'pomegranate',
  'pomelo',
  'ponkan',
  'potato',
  'prickly_lettuce',
  'prune',
  'pumpkin',
  'purple_cai-tai',
  'purslane',
  'radish',
  'rambutan',
  'raspberry',
  'rhubarb',
  'russula_virescens',
  'salak',
  'sand_pear',
  'scallion',
  'sea_of_nostoc_flagelliforme',
  'shallot',
  'shiitake',
  'sieva_bean',
  'sieva_bean_seed',
  'snake_gourd',
  'soybean',
  'soybean_seed',
  'soybean_sprouts',
  'spinach',
  'sprouting_broccoli',
  'straw_mushroom',
  'strawberry',
  'sugar_orange',
  'sugarcane',
  'sweet_potato',
  'sweetsop',
  'swiss_chard',
  'sword_bean',
  'syzygium_jambos',
  'taro',
  'termite_mushroom',
  'tomato',
  'tremella_fuciformis',
  'tricholoma_flavovirens',
  'trifoliate_orange',
  'walnuts',
  'wampee',
  'wasabi',
  'water_caltrop',
  'water_chestnuts',
  'water_spinach',
  'watercress',
  'watermelon',
  'wax_apple',
  'wax_gourd',
  'winter_jujube',
  'yacon',
  'yam_bean',
  'zha-tsai',
  'zizania_aquatica',
  'zucchini',
]

// Emoji mapping for rich UI presentation
export const INGREDIENT_EMOJIS = {
  apple: '🍎',
  apricot: '🍑',
  avocado: '🥑',
  banana: '🍌',
  basil: '🌿',
  bean: '🫘',
  beetroot: '🫐',
  bitter_gourd: '🥒',
  blueberry: '🫐',
  bottle_gourd: '🥬',
  brinjal: '🍆',
  broccoli: '🥦',
  cabbage: '🥬',
  capsicum: '🫑',
  carrot: '🥕',
  cauliflower: '🥦',
  celery: '🥬',
  cherry: '🍒',
  chive: '🌱',
  coconut: '🥥',
  coriander: '🌿',
  corn: '🌽',
  cucumber: '🥒',
  durian: '🍈',
  enoki_mushroom: '🍄',
  fig: '🫐',
  garlic: '🧄',
  ginger: '🫚',
  grape: '🍇',
  grapefruit: '🍊',
  guava: '🍈',
  kiwi_fruit: '🥝',
  lemon: '🍋',
  lettuce: '🥬',
  lime: '🍋‍🟩',
  mango: '🥭',
  mint: '🌿',
  mushroom: '🍄',
  olive: '🫒',
  onion: '🧅',
  orange: '🍊',
  oyster_mushroom: '🍄',
  papaya: '🍈',
  pea: '🫛',
  peach: '🍑',
  pear: '🍐',
  pepper: '🌶️',
  pineapple: '🍍',
  pistachio: '🥜',
  plum: '🫐',
  pomegranate: '🍎',
  potato: '🥔',
  pumpkin: '🎃',
  radish: '🥕',
  raspberry: '🍓',
  scallion: '🧅',
  shallot: '🧅',
  shiitake: '🍄',
  soybean: '🫘',
  spinach: '🥬',
  strawberry: '🍓',
  sweet_potato: '🍠',
  tomato: '🍅',
  walnuts: '🥜',
  watermelon: '🍉',
  zucchini: '🥒',
}

/**
 * Format internal class name for user-friendly display (e.g. agaricus_bisporus -> Agaricus Bisporus)
 */
export function formatIngredientName(name) {
  if (!name) return ''
  return name
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Fetch supported classes dynamically from backend with fallback
 */
export async function fetchSupportedClasses() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/vision/classes`)
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data.classes) && data.classes.length > 0) {
        return data.classes
      }
    }
  } catch (_) {
    // Keep fallback to static INGREDIENT_CLASSES
  }
  return INGREDIENT_CLASSES
}

/**
 * Check backend health status
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    })
    if (!response.ok) {
      return { available: false, error: `HTTP ${response.status}` }
    }
    const data = await response.json()
    return {
      available: data?.status === 'ok' && data?.services?.vision?.available === true,
      data,
    }
  } catch (err) {
    return {
      available: false,
      error: 'Unable to connect to DishGenie AI backend service.',
    }
  }
}

/**
 * Predicts ingredient from an uploaded file using the FastAPI CNN backend.
 *
 * @param {File} file - Image file from input or drag-and-drop
 * @returns {Promise<{ prediction: { name: string, confidence: number }, top_predictions: Array<{ name: string, confidence: number }> }>}
 */
export async function predictIngredient(file) {
  if (!file) {
    throw new Error('Please select an image file to analyze.')
  }

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type.toLowerCase())) {
    throw new Error('Unsupported file format. Please upload a JPG, JPEG, or PNG image.')
  }

  // File size validation (10MB limit)
  const MAX_FILE_SIZE = 10 * 1024 * 1024
  if (file.size > MAX_FILE_SIZE) {
    throw new Error('Image file is too large. Please select an image under 10MB.')
  }

  // Prepare multipart form data
  const formData = new FormData()
  formData.append('image', file)

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/vision/predict`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error('DishGenie backend is currently unavailable. Please make sure the local server is running and try again.')
  }

  // Handle non-200 responses
  if (!response.ok) {
    let errorDetail = "We couldn't analyze this image. Please check the backend service or try another photo."
    try {
      const errJson = await response.json()
      if (errJson.detail && typeof errJson.detail === 'string' && !errJson.detail.includes('Traceback')) {
        errorDetail = errJson.detail
      }
    } catch (_) {
      // Keep friendly message
    }
    throw new Error(errorDetail)
  }

  // Parse and validate response
  try {
    const data = await response.json()
    if (!data.prediction || !data.top_predictions) {
      throw new Error("We couldn't analyze this image. Please try again or choose another image.")
    }
    return data
  } catch (parseError) {
    throw new Error("We couldn't analyze this image. The server returned an unexpected response.")
  }
}

/**
 * Synthesizes a recipe using confirmed ingredients and preferences via the local FLAN-T5 GenAI service.
 *
 * @param {{ ingredients: string[], preferences: { diet: string, cuisine: string, cookingTime: number, difficulty: string, servings: number, additionalIngredients?: string } }} payload
 * @returns {Promise<{ success: boolean, recipe: Object | null, raw_text: string | null }>}
 */
export async function generateRecipe(payload) {
  if (!payload || !payload.ingredients || payload.ingredients.length === 0) {
    throw new Error('Please confirm at least one ingredient before generating a recipe.')
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/recipe/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch (networkError) {
    throw new Error('DishGenie backend is currently unavailable. Please make sure the local server is running and try again.')
  }

  if (!response.ok) {
    let errorDetail = 'Unable to generate your recipe.'
    try {
      const errJson = await response.json()
      if (errJson.detail && typeof errJson.detail === 'string' && !errJson.detail.includes('Traceback')) {
        errorDetail = errJson.detail
      }
    } catch (_) {
      // Keep friendly fallback
    }
    throw new Error(errorDetail)
  }

  try {
    const data = await response.json()
    return data
  } catch (parseError) {
    throw new Error('Unable to generate your recipe. The server returned an unparseable response.')
  }
}

