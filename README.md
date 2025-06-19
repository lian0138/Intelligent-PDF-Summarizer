**Introduction**  
This project, the Intelligent PDF Summarizer, emphasizes the capabilities of Azure Durable Functions in orchestrating complex document processing workflows. By leveraging Durable Functions, a serverless extension of Azure Functions, the application ensures reliable and ordered execution of tasks while integrating with Azure services like Storage and Cognitive Services, as well as OpenAI for summarization. 

**How It Works**  
Azure Durable Functions play a central role in the Intelligent PDF Summarizer by orchestrating a sequence of activities triggered by a PDF upload to an Azure Blob Storage 'input' container. The `process_document` orchestrator defines the workflow, coordinating steps like downloading the PDF, extracting text with Azure Cognitive Services, summarizing content via an AI model, and uploading the summary to an 'output' container. Durable Functions ensure sequential task execution using `context.call_activity_with_retry`, manage state persistence, and handle retries with configurable options (e.g., `RetryOptions`), making the process fault-tolerant and eliminating the need for external queues or state stores.

**What I Modified**  
While the core functionality of Azure Durable Functions remains unchanged, I adapted the project to address quota limitations in my Azure Student account by replacing Azure OpenAI with the OpenAI API in the `summarize_text` activity. The original code relied on Azure OpenAI with a generic input binding and environment-defined model, but my modification directly calls the OpenAI API with `gpt-3.5-turbo`. Importantly, the Durable Functions orchestration logic, including the `process_document` orchestrator and retry mechanisms, was unaffected, maintaining the robust workflow coordination and error handling that Durable Functions provide.

**Conclusion**  
In conclusion, the Intelligent PDF Summarizer project showcases the strength of Azure Durable Functions in managing intricate, multi-step workflows for document processing. Durable Functions simplify development by handling orchestration, state, and durability natively, ensuring reliable execution even in the face of transient failures. My adaptation to use the OpenAI API instead of Azure OpenAI reaffirms the flexibility of Durable Functions’ framework, as the core orchestration remained intact. This project illustrates how Durable Functions empower developers to build scalable, resilient applications with minimal infrastructure overhead.

**Youtube**
https://www.youtube.com/watch?v=lxWXHZe2-g8
