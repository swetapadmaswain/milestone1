# UI Design Prompt for Google Stitch - Restaurant Recommendation Frontend

Use this prompt with Google Stitch to generate UI mockups for the Next.js frontend of the AI-powered restaurant recommendation system.

---

## **Main Prompt for Landing Page**

```
Create a modern, minimalist landing page for an AI-powered restaurant recommendation web app called "DineSmart". 

Design specifications:
- Clean white background with subtle gradient accents in warm orange (#FF6B35) and deep blue (#1E3A8A)
- Hero section with large typography: "Discover Your Perfect Dining Experience" 
- Subheadline: "AI-powered restaurant recommendations personalized just for you"
- Central search bar with location icon, cuisine dropdown, and budget selector
- Three feature cards below hero showing: AI Recommendations, Personalized Learning, Smart Filters
- Modern sans-serif typography (Inter or similar)
- Rounded corners (8px radius) on all interactive elements
- Subtle shadows and hover states
- Mobile-responsive layout indication
- Include small AI robot mascot illustration in corner
- Navigation bar with logo, "How It Works", "Features", "Get Started" buttons
- Trust indicators: "10,000+ restaurants", "50,000+ happy diners", "4.9/5 rating"
- Call-to-action button: "Start Exploring" in primary orange color

Style: Modern SaaS landing page, clean and professional, food-tech aesthetic, warm and inviting colors
```

---

## **Prompt for Search & Filter Interface**

```
Design a restaurant search and filter interface for a Next.js web application.

Layout specifications:
- Left sidebar (30% width) with filter panel containing:
  * Location search with autocomplete and map pin icon
  * Budget slider with three segments: Low (â‚¹0-500), Medium (â‚¹500-1500), High (â‚¹1500+)
  * Cuisine multi-select with checkboxes (North Indian, South Indian, Chinese, Italian, etc.)
  * Rating filter with star ratings (1-5 stars, minimum 3.5 default)
  * Distance slider with "Within 5km" default
  * "Additional Preferences" text area for dietary restrictions
  * "Apply Filters" button in primary color
  * "Reset Filters" secondary button

- Right content area (70% width) showing:
  * Results count: "245 restaurants found in Bangalore"
  * Sort dropdown: "Recommended", "Rating", "Price: Low to High", "Distance"
  * Grid layout with restaurant cards (3 cards per row on desktop)

Style: Clean dashboard interface, sidebar navigation, card-based layout, modern filters with clear visual hierarchy, white background with subtle gray borders
```

---

## **Prompt for Restaurant Recommendation Card**

```
Design a restaurant recommendation card component for an AI restaurant finder app.

Card specifications:
- Card dimensions: 320px width, auto height
- White background with subtle shadow (0 2px 8px rgba(0,0,0,0.1))
- Rounded corners (12px radius)
- Top section: Restaurant hero image (16:9 aspect ratio) with overlay showing:
  * "AI Recommended" badge in top-left corner (green background, white text)
  * Heart icon for favoriting in top-right corner
  * "Open Now" status indicator in bottom-right

- Content section with padding:
  * Restaurant name: Large bold text (20px), truncate if too long
  * Location with map pin icon: "Koramangala, Bangalore" 
  * Cuisine tags: Small pill-shaped badges ("North Indian", "Mughlai")
  * Rating row: Star rating (4.5/5), review count (1,234 reviews), price indicator (â‚¹â‚¹â‚¹)
  * "Estimated cost for two: â‚¹800" in gray text

- AI Explanation section (highlighted with light blue background):
  * AI brain icon
  * "Why we recommend this:" heading
  * Personalized explanation text: "Based on your preference for spicy North Indian cuisine and high ratings in this area"
  * Confidence badge: "High Match" in green

- Action buttons at bottom:
  * "View Details" secondary button
  * "Get Directions" primary button with location icon

Style: Modern card design, food delivery app aesthetic, emphasis on AI recommendations, trust-building elements
```

---

## **Prompt for Restaurant Detail Page**

```
Design a restaurant detail page for a Next.js restaurant recommendation app.

Page layout:
- Full-width hero image (restaurant interior or food) with gradient overlay
- Back button and share icon in top navigation bar
- Restaurant name and key info overlaid on hero image

Content sections (single column, max-width 800px, centered):

1. **Header Section:**
   * Large restaurant name (32px bold)
   * Rating badge with stars and review count
   * Location with "Get Directions" button
   * Operating hours indicator
   * "Bookmark" and "Share" action buttons

2. **Quick Info Row:**
   * Four info cards horizontally: 
     - Average cost (â‚¹â‚¹â‚¹ icon + "â‚¹800 for two")
     - Cuisine type (utensils icon + "North Indian")
     - Delivery time (clock icon + "30-45 min")
     - Rating (star icon + "4.5/5")

3. **AI Recommendation Panel** (highlighted section):
   * "Personalized for You" header with sparkle icon
   * AI explanation: "This restaurant matches your preference for authentic North Indian cuisine and is highly rated by diners with similar tastes"
   * Match score: "92% Match" with progress bar
   * "Why this recommendation?" expandable section

4. **Menu Preview Section:**
   * "Popular Dishes" carousel with food images
   * Dish cards with name, price, and rating
   * "View Full Menu" link

5. **Reviews Section:**
   * "What Diners Say" header
   * 2-3 review cards with user avatar, name, rating, date, and review text
   * "Read All Reviews" button

6. **Similar Restaurants Section:**
   * "You May Also Like" header
   * Horizontal scroll of 3-4 recommendation cards

7. **Sticky Bottom Bar:**
   * "Call Restaurant" button
   * "Reserve Table" primary CTA button (full width on mobile)

Style: Rich detail page, emphasis on visual content, AI personalization highlighted, mobile-first responsive design, warm and inviting color scheme
```

---

## **Prompt for User Profile Dashboard**

```
Design a user profile dashboard for a restaurant recommendation app.

Dashboard layout with sidebar navigation:

**Left Sidebar Navigation:**
- User avatar and name at top
- Navigation menu items:
  * "My Recommendations" (active state)
  * "Saved Restaurants"
  * "Dining History"
  * "Preferences & Dietary"
  * "Settings"

**Main Content Area:**

1. **Profile Header:**
   * "Welcome back, [Name]!" greeting
   * Quick stats row: "15 restaurants saved", "8 reviews written", "Member since Jan 2024"
   * "Edit Profile" button

2. **Preference Overview Section:**
   * "Your Dining Preferences" card
   * Visual representation of:
     - Top cuisines (pie chart or horizontal bars): North Indian 45%, Italian 25%, Chinese 15%, etc.
     - Budget preference indicator: "Medium budget preferred"
     - Location preferences: "Koramangala, Indiranagar, JP Nagar"
   * "Update Preferences" link

3. **Personalization Learning Status:**
   * "AI Learning About Your Taste" card
   * Progress indicator: "Learning Progress: 78%"
   * Recent feedback: "You liked 3 North Indian restaurants this week"
   * "Help us improve: Rate your recent visits" CTA

4. **Recent Activity Timeline:**
   * "Recent Activity" section
   * Timeline of recent actions:
     - "Viewed Truffles restaurant" - 2 hours ago
     - "Liked Biryani Zone" - 1 day ago
     - "Saved Toit Brewpub" - 3 days ago
   * Each item has restaurant thumbnail and action icon

5. **Recommended for You Section:**
   * "Based on your recent activity" header
   * 2-3 restaurant recommendation cards (smaller size)

6. **Dining Insights (optional upgrade):**
   * "Your Dining Patterns" card
   * Monthly spending chart
   * Favorite dining days/time
   * Most visited cuisine types

Style: Personal dashboard, data visualization, user-centric design, clean card layout, friendly and approachable, modern web app aesthetic
```

---

## **Prompt for Feedback & Rating Interface**

```
Design a feedback and rating interface for restaurant recommendations.

Modal/Sheet layout:
- Slide-up modal or centered modal on desktop
- Close button (X) in top-right
- Title: "How was your experience at [Restaurant Name]?"

Rating Section:
- Large 5-star rating component (touch-friendly on mobile)
- Star labels below: "Poor", "Fair", "Good", "Very Good", "Excellent"
- Animated star fill on hover/tap

Quick Feedback Chips:
- "What did you like?" section with toggle chips:
  * "Food Quality"
  * "Service" 
  * "Ambience"
  * "Value for Money"
  * "Location"
  * "Wait Time"
- Multi-select with visual feedback (selected chips highlighted)

Detailed Review:
- "Tell us more" text area (optional)
- Character counter (max 500 chars)

Photos Upload:
- "Add Photos" button with camera icon
- Preview grid for uploaded images (max 4)

Recommendation Feedback:
- "Was this recommendation helpful?"
- Yes/No buttons with thumbs up/down icons
- "This helps us improve your future recommendations"

Action Buttons:
- "Submit Review" primary button (full width)
- "Skip for Now" secondary text button

Success State:
- Checkmark animation
- "Thanks for your feedback!"
- "This helps us find better restaurants for you"
- "Continue Exploring" button

Style: Friendly and encouraging, gamified feedback, mobile-optimized touch targets, warm colors for positive feedback, clean and simple form layout
```

---

## **Prompt for Mobile Navigation & Bottom Bar**

```
Design a mobile navigation bar for a restaurant recommendation app.

Bottom navigation bar (fixed, 64px height):
- 5 navigation items with icons and labels:
  1. "Home" - House icon (active state)
  2. "Search" - Search/magnifying glass icon
  3. "Explore" - Compass/discovery icon
  4. "Saved" - Heart/bookmark icon
  5. "Profile" - User avatar icon

Active state design:
- Icon filled with primary color (orange #FF6B35)
- Label text in primary color
- Subtle background highlight or dot indicator

Inactive state:
- Outline icon in gray (#6B7280)
- Label in gray

Center button (optional):
- "Nearby" floating action button in center
- Circular, raised with shadow
- Map/location icon

Top header bar:
- App logo on left
- Location selector ("Bangalore â†“") in center
- Notification bell icon on right

Style: Modern mobile app navigation, iOS/Android native feel, thumb-friendly touch targets, clear visual hierarchy, accessible color contrast
```

---

## **Prompt for Empty States & Loading**

```
Design empty state and loading screens for a restaurant recommendation app.

**Empty State - No Results:**
- Centered illustration: Person looking at empty plate or searching with magnifying glass
- Heading: "No restaurants found"
- Subtext: "Try adjusting your filters or search in a different location"
- Action buttons: "Clear Filters", "Try Nearby Areas"
- Warm, friendly illustration style (not sad or disappointing)

**Empty State - No Saved Restaurants:**
- Illustration: Empty heart or bookmark folder
- Heading: "No saved restaurants yet"
- Subtext: "Start exploring and save your favorite spots for quick access"
- CTA button: "Discover Restaurants"

**Loading State:**
- Skeleton screen for restaurant cards (3-4 placeholder cards)
- Pulsing shimmer effect in light gray
- "Finding the best restaurants for you..." text with animated dots
- Optional: Fun food-related loading animation (rotating plate, bouncing utensils)

**Error State:**
- Illustration: Broken robot or confused chef
- Heading: "Oops! Something went wrong"
- Subtext: "We're having trouble finding restaurants right now"
- "Try Again" button
- "Contact Support" secondary link

**First-Time User State:**
- Welcome illustration: Person celebrating with food
- "Welcome to DineSmart!" heading
- "Let's personalize your experience" subtext
- 3-step onboarding:
  1. "Select your location"
  2. "Choose your favorite cuisines"
  3. "Set your budget preference"
- "Get Started" button

Style: Friendly and encouraging empty states, polished loading animations, helpful error messages, onboarding flow with clear progress indicators
```

---

## **Technical Specifications to Include**

When generating these designs, specify these technical requirements:

```
Technical specifications for Next.js implementation:
- Responsive breakpoints: Mobile (320px-767px), Tablet (768px-1023px), Desktop (1024px+)
- Color palette:
  * Primary: #FF6B35 (warm orange)
  * Secondary: #1E3A8A (deep blue)
  * Success: #10B981 (green)
  * Warning: #F59E0B (amber)
  * Error: #EF4444 (red)
  * Neutral: #6B7280 (gray)
  * Background: #FFFFFF (white), #F9FAFB (light gray)
  * Text: #111827 (dark), #374151 (medium), #9CA3AF (light)
- Typography: Inter font family, weights 400, 500, 600, 700
- Spacing system: 4px base unit (4, 8, 12, 16, 24, 32, 48, 64px)
- Border radius: Small (4px), Medium (8px), Large (12px), XL (16px)
- Shadows: 
  * Small: 0 1px 2px rgba(0,0,0,0.05)
  * Medium: 0 4px 6px rgba(0,0,0,0.1)
  * Large: 0 10px 15px rgba(0,0,0,0.1)
- Animation: Smooth transitions (300ms ease-in-out), hover states with lift effect
- Icons: Lucide or Heroicons style (outline and filled variants)
- Accessibility: Minimum 4.5:1 contrast ratio, focus indicators, semantic HTML structure
```

---

## **Usage Instructions**

1. Copy the relevant prompt section based on which UI component you want to generate
2. Paste into Google Stitch with "Image generation" mode
3. Specify aspect ratio:
   - Landing page: 16:9 (desktop) or 9:16 (mobile)
   - Individual components: 4:3 or 1:1
   - Mobile screens: 9:16
4. Add "High quality", "Detailed", "UI/UX design" to improve generation quality
5. Iterate by refining the prompt based on initial results

---

## **Example Combined Prompt for Full Page**

```
Create a complete desktop mockup of an AI restaurant recommendation web app using Next.js.

Show the search results page with:
- Clean white background with orange (#FF6B35) accent colors
- Left sidebar with filters: location search, budget slider (low/medium/high), cuisine checkboxes, rating stars, distance slider
- Top bar showing "245 restaurants in Bangalore" with sort dropdown
- Main area showing 3 restaurant cards in a row with:
  * Food photography
  * Restaurant name, rating (4.5 stars), price level (â‚¹â‚¹â‚¹)
  * "AI Recommended" badges with explanations
  * Cuisine tags and location
  * Action buttons
- Include one card expanded to show detailed AI explanation section
- Modern, clean SaaS dashboard aesthetic
- Professional typography with Inter font
- Rounded corners and subtle shadows
- High-quality UI/UX design, detailed mockup, desktop web application
```

---

**Note to Developer:** These prompts are designed to work with Google Stitch (or similar AI image generators like Midjourney, DALL-E) to create UI mockups that can be used as reference for implementing the Next.js frontend. The generated images should capture the visual style, layout, and user experience flow before actual coding begins.
