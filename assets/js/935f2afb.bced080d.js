"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[53],{1109:e=>{e.exports=JSON.parse('{"pluginId":"default","version":"current","label":"Next","banner":null,"badge":false,"noIndex":false,"className":"docs-version-current","isLast":true,"docsSidebars":{"documentationSidebar":[{"type":"category","label":"Getting Started","items":[{"type":"link","label":"Introduction","href":"/weave/","docId":"introduction","unlisted":false},{"type":"link","label":"Quickstart: Track inputs & outputs of LLM calls","href":"/weave/quickstart","docId":"quickstart","unlisted":false},{"type":"link","label":"Tutorial: Build an Evaluation pipeline","href":"/weave/tutorial-eval","docId":"tutorial-eval","unlisted":false},{"type":"link","label":"Tutorial: Model-Based Evaluation of RAG applications","href":"/weave/tutorial-rag","docId":"tutorial-rag","unlisted":false}],"collapsed":false,"collapsible":false},{"type":"category","label":"Using Weave","items":[{"type":"category","label":"Core Types","items":[{"type":"link","label":"Models","href":"/weave/guides/core-types/models","docId":"guides/core-types/models","unlisted":false},{"type":"link","label":"Datasets","href":"/weave/guides/core-types/datasets","docId":"guides/core-types/datasets","unlisted":false},{"type":"link","label":"Evaluation","href":"/weave/guides/core-types/evaluations","docId":"guides/core-types/evaluations","unlisted":false}],"collapsed":false,"collapsible":false,"href":"/weave/guides/core-types/"},{"type":"category","label":"Tracking","items":[{"type":"link","label":"Objects","href":"/weave/guides/tracking/objects","docId":"guides/tracking/objects","unlisted":false},{"type":"link","label":"Ops","href":"/weave/guides/tracking/ops","docId":"guides/tracking/ops","unlisted":false},{"type":"link","label":"Tracing","href":"/weave/guides/tracking/tracing","docId":"guides/tracking/tracing","unlisted":false}],"collapsed":false,"collapsible":false,"href":"/weave/guides/tracking/"},{"type":"category","label":"Ecosystem","items":[{"type":"link","label":"OpenAI","href":"/weave/guides/ecosystem/openai","docId":"guides/ecosystem/openai","unlisted":false},{"type":"link","label":"Anthropic","href":"/weave/guides/ecosystem/anthropic","docId":"guides/ecosystem/anthropic","unlisted":false},{"type":"link","label":"MistralAI","href":"/weave/guides/ecosystem/mistral","docId":"guides/ecosystem/mistral","unlisted":false}],"collapsed":false,"collapsible":false,"href":"/weave/guides/ecosystem/"},{"type":"category","label":"Tools","items":[{"type":"link","label":"Serve","href":"/weave/guides/tools/serve","docId":"guides/tools/serve","unlisted":false},{"type":"link","label":"Deploy","href":"/weave/guides/tools/deploy","docId":"guides/tools/deploy","unlisted":false}],"collapsed":false,"collapsible":false,"href":"/weave/guides/tools/"},{"type":"link","label":"Platform & Security","href":"/weave/guides/platform/","docId":"guides/platform/index","unlisted":false}],"collapsed":false,"collapsible":false},{"type":"link","label":"API Reference","href":"/api-reference/python/weave"}],"apiReferenceSidebar":[{"type":"category","label":"Python API","collapsible":false,"collapsed":false,"items":[{"type":"link","label":"weave","href":"/weave/api-reference/python/weave","docId":"api-reference/python/weave","unlisted":false}],"href":"/weave/category/python-api"}]},"docs":{"api-reference/python/weave":{"id":"api-reference/python/weave","title":"weave","description":"These are the top-level functions in the import weave namespace.","sidebar":"apiReferenceSidebar"},"guides/core-types/datasets":{"id":"guides/core-types/datasets","title":"Datasets","description":"Datasets enable you to collect examples for evaluation and automatically track versions for accurate comparisons.","sidebar":"documentationSidebar"},"guides/core-types/evaluations":{"id":"guides/core-types/evaluations","title":"Evaluation","description":"Evaluation-driven development helps you reliably iterate on an application. The Evaluation class is designed to assess the performance of a Model on a given Dataset or set of examples using scoring functions.","sidebar":"documentationSidebar"},"guides/core-types/index":{"id":"guides/core-types/index","title":"Weave Core Types","description":"Weave Core Types are built with weave tracking, and contain everything you need to rapidly iterate on AI projects.","sidebar":"documentationSidebar"},"guides/core-types/models":{"id":"guides/core-types/models","title":"Models","description":"A Model is a combination of data (which can include configuration, trained model weights, or other information) and code that defines how the model operates. By structuring your code to be compatible with this API, you benefit from a structured way to version your application so you can more systematically keep track of your experiments.","sidebar":"documentationSidebar"},"guides/ecosystem/anthropic":{"id":"guides/ecosystem/anthropic","title":"Anthropic","description":"Weave automatically tracks and logs LLM calls made via the Anthropic Python library, after weave.init() is called.","sidebar":"documentationSidebar"},"guides/ecosystem/index":{"id":"guides/ecosystem/index","title":"Weave Ecosystem","description":"The Weave ecosystem contains automatic logging integrations for popular AI libraries, and Weave components for common AI workflows. Weave will automatically trace calls made via the following libraries:","sidebar":"documentationSidebar"},"guides/ecosystem/mistral":{"id":"guides/ecosystem/mistral","title":"MistralAI","description":"Weave automatically tracks and logs LLM calls made via the MistralAI Python library.","sidebar":"documentationSidebar"},"guides/ecosystem/openai":{"id":"guides/ecosystem/openai","title":"OpenAI","description":"Tracing","sidebar":"documentationSidebar"},"guides/platform/index":{"id":"guides/platform/index","title":"Platform & Security","description":"Weave is available on W&B SaaS Cloud which is a multi-tenant, fully-managed platform deployed in W&B\'s Google Cloud Platform (GCP) account in a North America region.","sidebar":"documentationSidebar"},"guides/tools/deploy":{"id":"guides/tools/deploy","title":"Deploy","description":"Deploy to GCP","sidebar":"documentationSidebar"},"guides/tools/index":{"id":"guides/tools/index","title":"Tools","description":"- serve: Serve Weave ops and models","sidebar":"documentationSidebar"},"guides/tools/serve":{"id":"guides/tools/serve","title":"Serve","description":"Given a Weave ref to any Weave Model you can run:","sidebar":"documentationSidebar"},"guides/tracking/index":{"id":"guides/tracking/index","title":"Tracking","description":"Weave track and versions objects and function calls.","sidebar":"documentationSidebar"},"guides/tracking/objects":{"id":"guides/tracking/objects","title":"Objects","description":"Weave\'s serialization layer saves and versions Python objects.","sidebar":"documentationSidebar"},"guides/tracking/ops":{"id":"guides/tracking/ops","title":"Ops","description":"A Weave op is a versioned function that automatically logs all calls.","sidebar":"documentationSidebar"},"guides/tracking/tracing":{"id":"guides/tracking/tracing","title":"Tracing","description":"Tracing is a powerful feature in Weave that allows you to track the inputs and outputs of functions seamlessly. Follow these steps to get started:","sidebar":"documentationSidebar"},"introduction":{"id":"introduction","title":"Introduction","description":"Weave is a lightweight toolkit for tracking and evaluating LLM applications, built by Weights & Biases.","sidebar":"documentationSidebar"},"quickstart":{"id":"quickstart","title":"Quickstart: Track inputs & outputs of LLM calls","description":"Follow these steps to track your first call or","sidebar":"documentationSidebar"},"tutorial-eval":{"id":"tutorial-eval","title":"Tutorial: Build an Evaluation pipeline","description":"To iterate on an application, we need a way to evaluate if it\'s improving. To do so, a common practice is to test it against the same set of examples when there is a change. Weave has a first-class way to track evaluations with Model & Evaluation classes. We have built the APIs to make minimal assumptions to allow for the flexibility to support a wide array of use-cases.","sidebar":"documentationSidebar"},"tutorial-rag":{"id":"tutorial-rag","title":"Tutorial: Model-Based Evaluation of RAG applications","description":"Retrieval Augmented Generation (RAG) is a common way of building Generative AI applications that have access to custom knowledge bases.","sidebar":"documentationSidebar"}}}')}}]);