/**
 * Sample TypeScript file for AST testing.
 */

import { add } from "./utils";
import axios from "axios";

export interface User {
  id: string;
  name: str;
}

export type UserRole = "admin" | "user";

export class UserService {
  /** Fetch user by ID */
  public async getUser(id: string): Promise<User> {
    return { id, name: "Alice" };
  }
}

export function formatUser(user: User): string {
  return `${user.name} (${user.id})`;
}

const internalHelper = () => {
  return true;
};
