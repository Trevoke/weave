"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[671],{667:(e,o,n)=>{n.r(o),n.d(o,{assets:()=>r,contentTitle:()=>i,default:()=>p,frontMatter:()=>t,metadata:()=>s,toc:()=>d});var l=n(5893),a=n(1151);const t={sidebar_position:0,hide_table_of_contents:!0},i="Local Models",s={id:"guides/integrations/local_models",title:"Local Models",description:"Many developers download and run open source models like LLama-3, Mixtral, Gemma, Phi and more locally. There are quite a few ways of running these models locally and Weave supports a few of them out of the box, as long as they support OpenAI SDK compatibility.",source:"@site/docs/guides/integrations/local_models.md",sourceDirName:"guides/integrations",slug:"/guides/integrations/local_models",permalink:"/weave/guides/integrations/local_models",draft:!1,unlisted:!1,editUrl:"https://github.com/wandb/weave/blob/master/docs/docs/guides/integrations/local_models.md",tags:[],version:"current",sidebarPosition:0,frontMatter:{sidebar_position:0,hide_table_of_contents:!0},sidebar:"documentationSidebar",previous:{title:"Open Router",permalink:"/weave/guides/integrations/openrouter"},next:{title:"LiteLLM",permalink:"/weave/guides/integrations/litellm"}},r={},d=[{value:"Wrap local model functions with <code>@weave.op()</code>",id:"wrap-local-model-functions-with-weaveop",level:2},{value:"Updating your OpenAI SDK code to use local models",id:"updating-your-openai-sdk-code-to-use-local-models",level:2},{value:"OpenAI SDK supported Local Model runners",id:"openai-sdk-supported-local-model-runners",level:2}];function c(e){const o={a:"a",code:"code",h1:"h1",h2:"h2",li:"li",ol:"ol",p:"p",pre:"pre",...(0,a.a)(),...e.components};return(0,l.jsxs)(l.Fragment,{children:[(0,l.jsx)(o.h1,{id:"local-models",children:"Local Models"}),"\n",(0,l.jsx)(o.p,{children:"Many developers download and run open source models like LLama-3, Mixtral, Gemma, Phi and more locally. There are quite a few ways of running these models locally and Weave supports a few of them out of the box, as long as they support OpenAI SDK compatibility."}),"\n",(0,l.jsxs)(o.h2,{id:"wrap-local-model-functions-with-weaveop",children:["Wrap local model functions with ",(0,l.jsx)(o.code,{children:"@weave.op()"})]}),"\n",(0,l.jsxs)(o.p,{children:["You can easily integrate Weave with any LLM yourself simply by initializing Weave with ",(0,l.jsx)(o.code,{children:"weave.init('<your-project-name>')"})," and then wrapping the calls to your LLMs with ",(0,l.jsx)(o.code,{children:"weave.op()"}),". See our guide on ",(0,l.jsx)(o.a,{href:"/guides/tracking/tracing",children:"tracing"})," for more details."]}),"\n",(0,l.jsx)(o.h2,{id:"updating-your-openai-sdk-code-to-use-local-models",children:"Updating your OpenAI SDK code to use local models"}),"\n",(0,l.jsx)(o.p,{children:"All of the frameworks of services that support OpenAI SDK compatibility require a few minor changes."}),"\n",(0,l.jsxs)(o.p,{children:["First and most important, is the ",(0,l.jsx)(o.code,{children:"base_url"})," change during the ",(0,l.jsx)(o.code,{children:"openai.OpenAI()"})," initialization."]}),"\n",(0,l.jsx)(o.pre,{children:(0,l.jsx)(o.code,{className:"language-python",children:"client = openai.OpenAI(\n    api_key='fake',\n    base_url=\"http://localhost:1234\",\n)\n"})}),"\n",(0,l.jsxs)(o.p,{children:["In the case of local models, the ",(0,l.jsx)(o.code,{children:"api_key"})," can be any string but it should be overriden, as otherwise OpenAI will try to use it from environment variables and show you an error."]}),"\n",(0,l.jsx)(o.h2,{id:"openai-sdk-supported-local-model-runners",children:"OpenAI SDK supported Local Model runners"}),"\n",(0,l.jsx)(o.p,{children:"Here's a list of apps that allows you to download and run models from Hugging Face on your computer, that support OpenAI SDK compatibility."}),"\n",(0,l.jsxs)(o.ol,{children:["\n",(0,l.jsxs)(o.li,{children:["Nomic ",(0,l.jsx)(o.a,{href:"https://www.nomic.ai/gpt4all",children:"GPT4All"})," - support via Local Server in settings (",(0,l.jsx)(o.a,{href:"https://docs.gpt4all.io/gpt4all_help/faq.html",children:"FAQ"}),")"]}),"\n",(0,l.jsxs)(o.li,{children:[(0,l.jsx)(o.a,{href:"https://lmstudio.ai/",children:"LMStudio"})," - Local Server OpenAI SDK support ",(0,l.jsx)(o.a,{href:"https://lmstudio.ai/docs/local-server",children:"docs"})]}),"\n",(0,l.jsxs)(o.li,{children:[(0,l.jsx)(o.a,{href:"https://ollama.com/",children:"Ollama"})," - ",(0,l.jsx)(o.a,{href:"https://github.com/ollama/ollama/blob/main/docs/openai.md",children:"Experimental Support"})," for OpenAI SDK"]}),"\n",(0,l.jsxs)(o.li,{children:["llama.cpp via ",(0,l.jsx)(o.a,{href:"https://llama-cpp-python.readthedocs.io/en/latest/server/",children:"llama-cpp-python"})," python package"]}),"\n",(0,l.jsxs)(o.li,{children:[(0,l.jsx)(o.a,{href:"https://github.com/Mozilla-Ocho/llamafile#other-example-llamafiles",children:"llamafile"})," - ",(0,l.jsx)(o.code,{children:"http://localhost:8080/v1"})," automatically supports OpenAI SDK on Llamafile run"]}),"\n"]})]})}function p(e={}){const{wrapper:o}={...(0,a.a)(),...e.components};return o?(0,l.jsx)(o,{...e,children:(0,l.jsx)(c,{...e})}):c(e)}},1151:(e,o,n)=>{n.d(o,{Z:()=>s,a:()=>i});var l=n(7294);const a={},t=l.createContext(a);function i(e){const o=l.useContext(t);return l.useMemo((function(){return"function"==typeof e?e(o):{...o,...e}}),[o,e])}function s(e){let o;return o=e.disableParentContext?"function"==typeof e.components?e.components(a):e.components||a:i(e.components),l.createElement(t.Provider,{value:o},e.children)}}}]);