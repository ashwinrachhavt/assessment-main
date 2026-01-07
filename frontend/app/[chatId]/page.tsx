"use client";

import { fetcher } from "@/utils/fetcher";
import { useEffect, useState } from "react";
import useSWR from "swr";

function ToolCallComponent({ message }: { message: any }) {
  if (message.tool_calls) {
    return message.tool_calls.map((s: any, i: number) => {
      return (
        <div
          key={`tool_call_${i}`}
          className={`max-w-md py-2 px-3 text-sm rounded-lg self-end bg-white border border-blue-950 shadow`}
        >
          Calling function <span className="font-mono">{s.function.name}</span>
          <p className="whitespace-pre-wrap font-mono text-sm">{s.function.arguments}</p>
        </div>
      );
    });
  }
}

function ToolResponseComponent({ message }: { message: any }) {
  return (
    <div
      className={`max-w-md py-2 px-3 text-sm rounded-lg self-end bg-white border border-blue-950 shadow`}
    >
      <div className="whitespace-pre-wrap font-mono text-sm">{message.content}</div>
    </div>
  );
}

function OpenAIConversationDisplay({ messages }: { messages: any[] }) {
  return (
    <div className="space-y-2 flex flex-col pb-4 px-2 overflow-y-scroll">
      {messages.map((s: any, i: number) => {
        if (s.role == "user") {
          return (
            <div
              key={`message_${i}`}
              className={`max-w-md py-2 px-3 text-sm flex items-center rounded-lg shadow self-start bg-red-950 text-white`}
            >
              <div>{s.content}</div>
            </div>
          );
        }
        if (s.role == "assistant") {
          if (s.tool_calls) {
            return <ToolCallComponent message={s} key={`message_${i}`} />;
          }
          return (
            <div
              key={`message_${i}`}
              className={`max-w-md py-2 px-3 text-sm rounded-lg shadow self-end bg-blue-950 text-white`}
            >
              <div>{s.content}</div>
            </div>
          );
        }
        if (s.role == "tool") {
          return <ToolResponseComponent message={s} key={`message_${i}`} />;
        }
      })}
    </div>
  );
}

export default function Home({ params }: { params: { chatId: string } }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [forms, setForms] = useState<any[]>([]);

  // TASK 2: Add state for editing forms
  const [editingFormId, setEditingFormId] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<any>({});

  const { data } = useSWR({ url: `chat/${params.chatId}` }, fetcher);
  const { data: formsData, mutate: mutateForms } = useSWR(
    { url: `chat/${params.chatId}/forms` },
    fetcher,
  );

  useEffect(() => {
    if (data) {
      setMessages(data.messages);
    }
  }, [data]);

  useEffect(() => {
    if (formsData) {
      setForms(formsData);
    }
  }, [formsData]);

  async function generateResponse() {
    if (!input) {
      return;
    }

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");

    const data = {
      messages: newMessages,
    };

    const resp = await fetch(`http://localhost:8000/chat/${params.chatId}`, {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (resp.ok) {
      const json = await resp.json();
      setMessages(json.messages);
      mutateForms(); // Refresh forms after chat update
    }
  }

  // TASK 2: Handle edit button click
  const startEditing = (form: any) => {
    setEditingFormId(form.id);
    setEditFormData({
      name: form.name,
      email: form.email,
      phone_number: form.phone_number,
      status: form.status,
    });
  };

  // TASK 2: Handle form update via REST API
  const handleUpdateForm = async (formId: string) => {
    try {
      const resp = await fetch(`http://localhost:8000/forms/${formId}`, {
        method: "PUT",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editFormData),
      });

      if (resp.ok) {
        alert("Form updated successfully!");
        setEditingFormId(null);
        mutateForms(); // Refresh forms list
      } else {
        const error = await resp.json();
        alert(`Error: ${error.detail || "Failed to update form"}`);
      }
    } catch (error) {
      console.error("Error updating form:", error);
      alert("Failed to update form");
    }
  };

  // TASK 2: Handle form delete via REST API
  const handleDeleteForm = async (formId: string) => {
    if (!confirm("Are you sure you want to delete this form?")) return;

    try {
      const resp = await fetch(`http://localhost:8000/forms/${formId}`, {
        method: "DELETE",
      });

      if (resp.ok) {
        alert("Form deleted successfully!");
        mutateForms(); // Refresh forms list
      } else {
        const error = await resp.json();
        alert(`Error: ${error.detail || "Failed to delete form"}`);
      }
    } catch (error) {
      console.error("Error deleting form:", error);
      alert("Failed to delete form");
    }
  };

  const cancelEditing = () => {
    setEditingFormId(null);
    setEditFormData({});
  };

  return (
    <main className="flex min-h-screen flex-col items-center space-y-4 p-24">
      <h1 className="text-xl font-semibold">Chat Window</h1>
      <div className="grow w-1/2 border border-gray-300 bg-gray-50 flex flex-col-reverse rounded-lg overflow-y-scroll">
        <OpenAIConversationDisplay messages={messages} />
      </div>

      {/* TASK 1 & 2: Display forms with edit/delete functionality */}
      {forms.length > 0 && (
        <div className="w-1/2 border border-gray-300 bg-gray-50 rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">Submitted Interest Forms</h2>
          <div className="space-y-3">
            {forms.map((form: any) => {
              const submittedAt = form?.created_at
                ? new Date(
                    form.created_at.endsWith("Z") ? form.created_at : form.created_at + "Z",
                  ).toLocaleString()
                : "Unknown";

              const statusLabel =
                form?.status === 1
                  ? "TO DO"
                  : form?.status === 2
                    ? "IN PROGRESS"
                    : form?.status === 3
                      ? "COMPLETED"
                      : "Not set";

              const isEditing = editingFormId === form.id;

              return (
                <div
                  key={form.id}
                  className="rounded-md border border-neutral-200 bg-white p-3 shadow-sm"
                >
                  {isEditing ? (
                    // TASK 2: Edit mode
                    <div className="space-y-2">
                      <div>
                        <label className="block text-xs font-semibold mb-1">Name</label>
                        <input
                          type="text"
                          value={editFormData.name || ""}
                          onChange={(e) =>
                            setEditFormData({ ...editFormData, name: e.target.value })
                          }
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1">Email</label>
                        <input
                          type="email"
                          value={editFormData.email || ""}
                          onChange={(e) =>
                            setEditFormData({ ...editFormData, email: e.target.value })
                          }
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1">Phone</label>
                        <input
                          type="text"
                          value={editFormData.phone_number || ""}
                          onChange={(e) =>
                            setEditFormData({ ...editFormData, phone_number: e.target.value })
                          }
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1">Status</label>
                        <select
                          value={editFormData.status || ""}
                          onChange={(e) =>
                            setEditFormData({
                              ...editFormData,
                              status: e.target.value ? parseInt(e.target.value) : null,
                            })
                          }
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                        >
                          <option value="">Not set</option>
                          <option value="1">TO DO</option>
                          <option value="2">IN PROGRESS</option>
                          <option value="3">COMPLETED</option>
                        </select>
                      </div>
                      <div className="flex space-x-2 mt-3">
                        <button
                          onClick={() => handleUpdateForm(form.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
                        >
                          Save
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="bg-gray-400 hover:bg-gray-500 text-white text-sm px-3 py-1 rounded"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    // TASK 1 & 2: View mode
                    <div>
                      <div className="text-sm">
                        <span className="font-semibold">Name:</span> {form.name}
                      </div>
                      <div className="text-sm">
                        <span className="font-semibold">Email:</span> {form.email}
                      </div>
                      <div className="text-sm">
                        <span className="font-semibold">Phone:</span> {form.phone_number}
                      </div>
                      <div className="text-sm">
                        <span className="font-semibold">Status:</span> {statusLabel}
                      </div>
                      <div className="text-xs text-neutral-600 mt-1">Submitted: {submittedAt}</div>

                      {/* TASK 2: Edit and Delete buttons */}
                      <div className="flex space-x-2 mt-3">
                        <button
                          onClick={() => startEditing(form)}
                          className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteForm(form.id)}
                          className="bg-red-600 hover:bg-red-700 text-white text-sm px-3 py-1 rounded"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex w-1/2 space-x-2">
        <input
          type="text"
          onChange={(e) => setInput(e.target.value)}
          value={input}
          onKeyPress={(e) => e.key === "Enter" && generateResponse()}
          className="bg-gray-50 grow border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
          placeholder="Type a message..."
        />
        <button
          onClick={() => generateResponse()}
          className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm w-full sm:w-auto px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
        >
          Send
        </button>
      </div>
    </main>
  );
}
