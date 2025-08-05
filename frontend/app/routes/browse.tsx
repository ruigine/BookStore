import { useState } from "react";

export default function BrowseBooks() {
  const [name, setName] = useState(""); // Like Vue's `data()`
  const title = "Welcome!";             // Static value

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">{title}</h1>

      <input
        value={name}
        onChange={(e) => setName(e.target.value)} // Like `v-model`
        placeholder="Enter your name"
        className="border border-gray-300 p-2 rounded"
      />

      <p className="mt-4">Hello, {name || "stranger"}!</p>
    </div>
  );
}