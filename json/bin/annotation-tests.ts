#!/usr/bin/env deno
import { validate } from "npm:@hyperjump/json-schema/draft-07";
import { BASIC } from "npm:@hyperjump/json-schema/experimental";

const validateTestSuite = await validate("./annotations/test-suite.schema.json");

console.log("Validating annotation tests ...");

let isValid = true;
for await (const entry of Deno.readDir("./annotations/tests")) {
  if (entry.isFile) {
    const json = await Deno.readTextFile(`./annotations/tests/${entry.name}`);
    const suite = JSON.parse(json);

    const output = validateTestSuite(suite, BASIC);

    if (output.valid) {
      console.log(`\x1b[32m✔\x1b[0m ${entry.name}`);
    } else {
      isValid = false;
      console.log(`\x1b[31m✖\x1b[0m ${entry.name}`);
      console.log(output);
    }
  }
}

console.log("Done.");

if (!isValid) {
  Deno.exit(1);
}
