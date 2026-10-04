// Material Design icons for the diagrams, so a Mermaid node can show the
// same icon as the rest of the site: `id@{ icon: "mdi:database" }`.
// Only the icons the diagrams use are bundled. To add one, copy the
// contents of its <svg> from material/templates/.icons/material/<name>.svg
// in the mkdocs-material package. Loaded by overrides/main.html on pages
// with a diagram, before Material renders them.

// Material draws diagrams in a shadow root, out of reach of the site's
// stylesheet, and styles them through the themeCSS it passes to
// mermaid.initialize. Icon nodes are not covered there, so these rules are
// appended to it: the theme's own variables, so they follow light and dark.
const ICON_NODE_CSS = `
  .icon-shape > g:first-child > path:first-child { fill: var(--md-mermaid-node-bg-color); }
  .icon-shape > g:first-child > path:nth-child(2) { stroke: var(--md-mermaid-node-fg-color); }
  .icon-shape svg path { fill: var(--md-mermaid-node-fg-color); }
  .icon-shape .labelBkg, .icon-shape .nodeLabel, .icon-shape .nodeLabel p { background: transparent !important; }
  .icon-shape .label rect { fill: transparent !important; }
  .icon-shape .nodeLabel, .icon-shape .nodeLabel p { color: var(--md-mermaid-label-fg-color) !important; }
`;

const initialize = mermaid.initialize.bind(mermaid);
mermaid.initialize = (config = {}) =>
  initialize({ ...config, themeCSS: (config.themeCSS || "") + ICON_NODE_CSS });

mermaid.registerIconPacks([
  {
    name: "mdi",
    icons: {
  "prefix": "mdi",
  "width": 24,
  "height": 24,
  "icons": {
    "api": {
      "body": "<path d=\"M7 7H5a2 2 0 0 0-2 2v8h2v-4h2v4h2V9a2 2 0 0 0-2-2m0 4H5V9h2m7-2h-4v10h2v-4h2a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2m0 4h-2V9h2m6 0v6h1v2h-4v-2h1V9h-1V7h4v2Z\"/>"
    },
    "cloud-download": {
      "body": "<path d=\"M6.5 20q-2.28 0-3.89-1.57Q1 16.85 1 14.58q0-1.95 1.17-3.48 1.18-1.53 3.08-1.95.58-2.02 2.14-3.4Q8.95 4.38 11 4.08v8.07L9.4 10.6 8 12l4 4 4-4-1.4-1.4-1.6 1.55V4.08q2.58.35 4.29 2.31T19 11q1.73.2 2.86 1.5 1.14 1.28 1.14 3 0 1.88-1.31 3.19T18.5 20Z\"/>"
    },
    "database-sync": {
      "body": "<path d=\"M19 12v1.5a4 4 0 0 1 4 4c0 .82-.25 1.58-.67 2.21l-1.09-1.09c.17-.34.26-.72.26-1.12A2.5 2.5 0 0 0 19 15v1.5l-2.25-2.25zm0 11v-1.5a4 4 0 0 1-4-4c0-.82.25-1.58.67-2.21l1.09 1.09c-.17.34-.26.72-.26 1.12A2.5 2.5 0 0 0 19 20v-1.5l2.25 2.25zM12 3c4.42 0 8 1.79 8 4s-3.58 4-8 4-8-1.79-8-4 3.58-4 8-4M4 9c0 2.21 3.58 4 8 4 1.11 0 2.17-.11 3.14-.32-.95.86-1.64 1.99-1.96 3.28L12 16c-4.42 0-8-1.79-8-4zm16 0v2h-.5l-.6.03c.7-.6 1.1-1.29 1.1-2.03M4 14c0 2.21 3.58 4 8 4l1-.03c.09 1.06.42 2.03.95 2.91L12 21c-4.42 0-8-1.79-8-4z\"/>"
    },
    "database": {
      "body": "<path d=\"M12 3C7.58 3 4 4.79 4 7s3.58 4 8 4 8-1.79 8-4-3.58-4-8-4M4 9v3c0 2.21 3.58 4 8 4s8-1.79 8-4V9c0 2.21-3.58 4-8 4s-8-1.79-8-4m0 5v3c0 2.21 3.58 4 8 4s8-1.79 8-4v-3c0 2.21-3.58 4-8 4s-8-1.79-8-4\"/>"
    },
    "file-document-multiple": {
      "body": "<path d=\"M4 4v18h16v2H4c-1.1 0-2-.9-2-2V4zm11 3h5.5L15 1.5zM8 0h8l6 6v12c0 1.11-.89 2-2 2H8a2 2 0 0 1-2-2V2c0-1.11.89-2 2-2m9 16v-2H8v2zm3-4v-2H8v2z\"/>"
    },
    "chart-box": {
      "body": "<path d=\"M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2M9 17H7v-7h2zm4 0h-2V7h2zm4 0h-2v-4h2z\"/>"
    },
    "web": {
      "body": "<path d=\"M16.36 14c.08-.66.14-1.32.14-2s-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2m-5.15 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95a8.03 8.03 0 0 1-4.33 3.56M14.34 14H9.66c-.1-.66-.16-1.32-.16-2s.06-1.35.16-2h4.68c.09.65.16 1.32.16 2s-.07 1.34-.16 2M12 19.96c-.83-1.2-1.5-2.53-1.91-3.96h3.82c-.41 1.43-1.08 2.76-1.91 3.96M8 8H5.08A7.92 7.92 0 0 1 9.4 4.44C8.8 5.55 8.35 6.75 8 8m-2.92 8H8c.35 1.25.8 2.45 1.4 3.56A8 8 0 0 1 5.08 16m-.82-2C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2s.06 1.34.14 2M12 4.03c.83 1.2 1.5 2.54 1.91 3.97h-3.82c.41-1.43 1.08-2.77 1.91-3.97M18.92 8h-2.95a15.7 15.7 0 0 0-1.38-3.56c1.84.63 3.37 1.9 4.33 3.56M12 2C6.47 2 2 6.5 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2\"/>"
    },
    "calendar-sync": {
      "body": "<path d=\"M18 11v1.5c3.19 0 5.09 3.55 3.33 6.21l-1.09-1.09C21.06 15.96 19.85 14 18 14v1.5l-2.25-2.25zm0 11v-1.5c-3.19 0-5.09-3.55-3.33-6.21l1.09 1.09C14.94 17.04 16.15 19 18 19v-1.5l2.25 2.25zm1-19h-1V1h-2v2H8V1H6v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h9a5.9 5.9 0 0 1-1.5-2H5V8h14v2.59c.71.11 1.39.35 2 .72V5a2 2 0 0 0-2-2\"/>"
    },
    "history": {
      "body": "<path d=\"M13.5 8H12v5l4.28 2.54.72-1.21-3.5-2.08zM13 3a9 9 0 0 0-9 9H1l3.96 4.03L9 12H6a7 7 0 0 1 7-7 7 7 0 0 1 7 7 7 7 0 0 1-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.9 8.9 0 0 0 13 21a9 9 0 0 0 9-9 9 9 0 0 0-9-9\"/>"
    },
    "check-decagram": {
      "body": "<path d=\"m23 12-2.44-2.78.34-3.68-3.61-.82-1.89-3.18L12 3 8.6 1.54 6.71 4.72l-3.61.81.34 3.68L1 12l2.44 2.78-.34 3.69 3.61.82 1.89 3.18L12 21l3.4 1.46 1.89-3.18 3.61-.82-.34-3.68zm-13 5-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9z\"/>"
    },
    "close-octagon": {
      "body": "<path d=\"M8.27 3 3 8.27v7.46L8.27 21h7.46L21 15.73V8.27L15.73 3M8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59 15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41\"/>"
    },
    "file-replace": {
      "body": "<path d=\"M14 12h5.5L14 6.5zM8 5h7l6 6v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-3h5v2l4-3-4-3v2H6V7a2 2 0 0 1 2-2m5.5-2H4v13h2v2H4a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h7.5z\"/>"
    },
    "delete-clock": {
      "body": "<path d=\"M15 13h1.5v2.82l2.44 1.41-.75 1.3L15 16.69zm8 3c0 3.87-3.13 7-7 7-1.91 0-3.64-.76-4.9-2H8c-1.1 0-2-.9-2-2V7h12v2.29c2.89.86 5 3.54 5 6.71m-7-5c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5m3-7v2H5V4h3.5l1-1h5l1 1z\"/>"
    },
    "shield-account": {
      "body": "<path d=\"M12 1 3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5zm0 4a3 3 0 0 1 3 3 3 3 0 0 1-3 3 3 3 0 0 1-3-3 3 3 0 0 1 3-3m5.13 12A9.7 9.7 0 0 1 12 20.92 9.7 9.7 0 0 1 6.87 17c-.34-.5-.63-1-.87-1.53 0-1.65 2.71-3 6-3s6 1.32 6 3c-.24.53-.53 1.03-.87 1.53\"/>"
    },
    "account-group": {
      "body": "<path d=\"M12 5.5A3.5 3.5 0 0 1 15.5 9a3.5 3.5 0 0 1-3.5 3.5A3.5 3.5 0 0 1 8.5 9 3.5 3.5 0 0 1 12 5.5M5 8c.56 0 1.08.15 1.53.42-.15 1.43.27 2.85 1.13 3.96C7.16 13.34 6.16 14 5 14a3 3 0 0 1-3-3 3 3 0 0 1 3-3m14 0a3 3 0 0 1 3 3 3 3 0 0 1-3 3c-1.16 0-2.16-.66-2.66-1.62a5.54 5.54 0 0 0 1.13-3.96c.45-.27.97-.42 1.53-.42M5.5 18.25c0-2.07 2.91-3.75 6.5-3.75s6.5 1.68 6.5 3.75V20h-13zM0 20v-1.5c0-1.39 1.89-2.56 4.45-2.9-.59.68-.95 1.62-.95 2.65V20zm24 0h-3.5v-1.75c0-1.03-.36-1.97-.95-2.65 2.56.34 4.45 1.51 4.45 2.9z\"/>"
    },
    "table": {
      "body": "<path d=\"M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 4v4h6V8zm8 0v4h6V8zm-8 6v4h6v-4zm8 0v4h6v-4z\"/>"
    }
  }
},
  },
]);
