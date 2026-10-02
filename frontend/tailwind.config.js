/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Unique minimal mineral light palette (No blue, No purple, No orange)
        ink: "#F8F8F6",
        paper: "#18181B",
        "paper-muted": "#71717A",
        "paper-subtle": "#A1A1AA",
        signal: "#18181B",
        agent: "#27272A",
        warn: "#DC2626",
        ok: "#15803D",
        card: "#FFFFFF",
        surface: {
          canvas: "#F8F8F6",
          card: "#FFFFFF",
          subtle: "#F4F4F2",
          border: "#E4E4E0",
          borderHover: "#D4D4D0",
        }
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        display: ["'Plus Jakarta Sans'", "Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["'JetBrains Mono'", "'IBM Plex Mono'", "monospace"],
      },
      fontSize: {
        xs: ["12px", "16px"],
        sm: ["13px", "20px"],
        base: ["14px", "22px"],
        lg: ["16px", "24px"],
        xl: ["18px", "26px"],
        "2xl": ["22px", "30px"],
        "3xl": ["28px", "36px"],
        "4xl": ["36px", "44px"],
        "5xl": ["48px", "56px"],
      },
      boxShadow: {
        xs: "0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        sm: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.03)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.02)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.02)",
        xl: "0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02)",
      },
      borderRadius: {
        xl: "14px",
        lg: "10px",
        md: "8px",
        sm: "6px",
      }
    },
  },
  plugins: [],
}
