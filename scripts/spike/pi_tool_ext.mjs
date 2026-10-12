export default function retrieveExtension(pi) {
  pi.registerTool({
    name: "retrieve_transcripts",
    description: "Retrieve podcast transcripts from Lenny's podcast archives. MUST be called first to get facts.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" }
      },
      required: ["query"]
    },
    async execute(id, params) {
      console.error("[PI TOOL CALLED] retrieve_transcripts with params:", JSON.stringify(params));
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify([
              {
                guest: "Ada Chen Rekhi",
                title: "Knowing When It Is Time to Leave Your Job",
                text: "The Energy & Learning Matrix tracks energy and skill acquisition across a 60-day window. If both are low for more than 4 consecutive weeks, staying becomes an active liability."
              },
              {
                guest: "Ada Chen Rekhi",
                title: "Knowing When It Is Time to Leave Your Job",
                text: "Before resigning, run three diagnostic checks: exhaust internal team transfers, isolate manager vs company friction, and ensure 6 months of financial runway."
              }
            ])
          }
        ]
      };
    }
  });
}
