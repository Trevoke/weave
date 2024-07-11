import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  documentationSidebar: [
    // {
    //   type: "category",
    //   label: "Getting Started",
    //   items: [{ type: "autogenerated", dirName: "get-started" }],
    // },
    {
      type: "category",
      label: "Getting Started",
      collapsed: false,
      items: ["introduction", "quickstart", "tutorial-eval", "tutorial-rag"],
    },
    {
      type: "category",
      label: "Using Weave",
      collapsed: false,
      items: [
        {
          type: "category",
          label: "Core Types",
          link: { type: "doc", id: "guides/core-types/index" },
          collapsed: false,
          items: [
            "guides/core-types/models",
            "guides/core-types/datasets",
            "guides/core-types/evaluations",
          ],
        },
        {
          type: "category",
          label: "Tracking",
          link: { type: "doc", id: "guides/tracking/index" },
          collapsed: false,
          items: [
            "guides/tracking/objects",
            "guides/tracking/ops",
            "guides/tracking/tracing",
            "guides/tracking/feedback",
          ],
        },
        {
          type: "category",
          label: "Integrations",
          link: { type: "doc", id: "guides/integrations/index" },
          collapsed: false,
          items: [
            "guides/integrations/openai",
            "guides/integrations/anthropic",
            "guides/integrations/mistral",
            "guides/integrations/llamaindex",
            "guides/integrations/dspy",
            "guides/integrations/google-gemini",
            "guides/integrations/together_ai",
            "guides/integrations/openrouter",
            "guides/integrations/local_models",
          ],
        },
        {
          type: "category",
          label: "Tools",
          link: { type: "doc", id: "guides/tools/index" },
          collapsed: false,
          items: ["guides/tools/serve", "guides/tools/deploy"],
        },
        {
          type: "doc",
          id: "guides/platform/index",
        },
      ],
    },
    {
      type: "link",
      label: "API Reference",
      href: "/api-reference/python/weave",
    },
    {
      type: "category",
      label: "Weave Cookbooks",
      link: { type: "doc", id: "guides/cookbooks/index" },
      collapsed: false,
      items: [
        {
          type: "category",
          label: "Building an English Teaching Assistant using RAG",
          link: { type: "doc", id: "guides/cookbooks/llamaindex_rag_ncert/intro" },
          items: [
            "guides/cookbooks/llamaindex_rag_ncert/vector_index",
            "guides/cookbooks/llamaindex_rag_ncert/query_engine",
            "guides/cookbooks/llamaindex_rag_ncert/prompt_engineering",
            "guides/cookbooks/llamaindex_rag_ncert/evaluation",
          ],
        }
      ],
    }
  ],
  // { type: "autogenerated", dirName: "get-started" }],
  apiReferenceSidebar: [{ type: "autogenerated", dirName: "api-reference" }],

  // But you can create a sidebar manually
  /*
  tutorialSidebar: [
    'intro',
    'hello',
    {
      type: 'category',
      label: 'Tutorial',
      items: ['tutorial-basics/create-a-document'],
    },
  ],
   */
};

export default sidebars;
